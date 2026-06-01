import pytest

from agentmemory.core.models import (
    CrystalCreateRequest,
    ForgetRequest,
    ContextRequest,
    LessonRecallRequest,
    MaintenanceRunRequest,
    ObserveRequest,
    RememberRequest,
    SearchRequest,
    GovernanceImportRequest,
    WikiConsolidateRequest,
    WikiFileAnswerRequest,
    WikiReflectRequest,
    WikiRebuildRequest,
    WikiUpdateRequest,
)
from agentmemory.core.search import MemorySearchService
from agentmemory.core.service import MemoryCoreService, MemoryNotFoundError
from agentmemory.state import StateKV
from conftest import StubEmbeddingProvider, StubLLMProvider, ai_settings


def test_observe_creates_project_observations(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())

    first = service.observe(
        ObserveRequest(
            content="Read PROJECT.md and confirmed the bootstrap scope.",
            project="agentmemory",
            cwd="/repo",
            files=["PROJECT.md"],
            concepts=["bootstrap"],
            language="en",
        ),
    )
    second = service.observe(
        ObserveRequest(
            content="Added memory core design notes.",
            project="agentmemory",
            cwd="/repo",
            language="en",
        ),
    )

    projects = service.list_projects()
    observations = service.list_observations()
    audit = service.list_audit()

    assert first.observation.project == "agentmemory"
    assert second.observation.projectId == first.observation.projectId
    assert len(projects) == 1
    assert len(observations) == 2
    assert {item.projectId for item in observations} == {projects[0].id}
    assert [record.action for record in audit] == ["observe", "observe"]
    assert first.processingJob is not None
    assert first.processingJob.status == "pending"
    assert first.summary is None
    assert first.memoryCandidates == []

    maintenance = service.run_maintenance(MaintenanceRunRequest(limit=5))

    assert [job["status"] for job in maintenance.llm["jobs"]] == ["done", "done"]
    assert len(service.list_summaries()) == 2
    assert len(service.list_memory_candidates()) == 2
    actions = [record.action for record in service.list_audit()]
    assert actions[:2] == ["observe", "observe"]
    assert actions.count("llm_processing_done") == 2
def test_observe_saves_summary_candidates_and_job_without_auto_remember(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())

    result = service.observe(
        ObserveRequest(
            content="CLI local writes must require AI settings.",
            language="en",
        ),
    )

    summaries = service.list_summaries()
    candidates = service.list_memory_candidates()
    jobs = service.list_llm_processing_jobs()
    memories = service.list_memories()

    assert result.processingJob is not None
    assert result.processingJob.status == "pending"
    assert result.summary is None
    assert result.memoryCandidates == []
    assert summaries == []
    assert candidates == []
    assert jobs[0].summaryId is None
    assert jobs[0].candidateIds == []
    assert memories == []

    service.run_maintenance(MaintenanceRunRequest(limit=5))
    summaries = service.list_summaries()
    candidates = service.list_memory_candidates()
    jobs = service.list_llm_processing_jobs()

    assert summaries[0].content == "Stub summary"
    assert candidates[0].content == "Remember the tested memory processing behavior."
    assert jobs[0].status == "done"
    assert jobs[0].summaryId == summaries[0].id
    assert jobs[0].candidateIds == [candidates[0].id]


def test_observe_preserves_observation_when_llm_processing_fails(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider(fail=True))

    result = service.observe(
        ObserveRequest(
            content="This observation should survive LLM failure.",
            language="en",
        ),
    )

    jobs = service.list_llm_processing_jobs()
    summaries = service.list_summaries()
    candidates = service.list_memory_candidates()
    audit = service.list_audit()

    assert result.observationId.startswith("obs_")
    assert result.processingJob is not None
    assert result.processingJob.status == "pending"
    assert result.summary is None
    assert result.memoryCandidates == []
    assert jobs[0].status == "pending"
    assert jobs[0].lastError is None
    assert summaries == []
    assert candidates == []
    assert audit[-1].action == "observe"

    service.run_maintenance(MaintenanceRunRequest(limit=5))
    jobs = service.list_llm_processing_jobs()
    assert jobs[0].status == "failed"
    assert "stub llm failure" in (jobs[0].lastError or "")
    assert "llm_processing_failed" in [record.action for record in service.list_audit()]


def test_remember_saves_memory_and_audit(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))

    result = service.remember(
        RememberRequest(
            content="Use Python/FastAPI for the backend service foundation.",
            type="decision",
            concepts=["fastapi", "backend"],
            files=["PROJECT.md"],
            language="en",
        ),
    )

    memories = service.list_memories()
    audit = service.list_audit()

    assert result.memoryId.startswith("mem_")
    assert len(memories) == 1
    assert memories[0].content == "Use Python/FastAPI for the backend service foundation."
    assert memories[0].concepts == ["fastapi", "backend"]
    assert audit[-1].action == "remember"
    assert audit[-1].targetId == result.memoryId


def test_multilingual_duplicate_candidate_is_not_merged(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))

    service.remember(
        RememberRequest(
            content="后端选择 FastAPI，因为 Python 的 RAG 生态更成熟。",
            type="decision",
            language="zh",
        ),
    )
    service.remember(
        RememberRequest(
            content="Backend uses FastAPI because Python has a stronger RAG ecosystem.",
            type="decision",
            language="en",
        ),
    )

    memories = service.list_memories()

    assert len(memories) == 2
    assert {memory.language for memory in memories} == {"zh", "en"}
    assert all(memory.duplicateOf is None for memory in memories)


def test_export_data_writes_audit_and_includes_governance_records(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())
    service.observe(ObserveRequest(content="Export should include observations.", language="en"))
    service.remember(RememberRequest(content="Export should include memories.", language="en"))
    service.run_maintenance(MaintenanceRunRequest(limit=5))

    exported = service.export_data(source="test")

    assert exported.version
    assert exported.schemaVersion == 2
    assert len(exported.projects) == 1
    assert exported.exportedAt
    assert len(exported.observations) == 1
    assert len(exported.memories) == 1
    assert len(exported.summaries) == 1
    assert len(exported.memoryCandidates) == 1
    assert len(exported.llmProcessingJobs) == 1
    assert exported.audit[-1].action == "export"
    assert exported.audit[-1].targetType == "governance"
    assert exported.audit[-1].details["memories"] == 1


def test_import_data_restores_export_into_fresh_searchable_store(tmp_path):
    source = MemoryCoreService(StateKV(tmp_path / "source.sqlite3"), llm=StubLLMProvider())
    source.observe(ObserveRequest(content="Import restores observations.", language="en"))
    source.remember(RememberRequest(content="Import restores searchable memories.", language="en", concepts=["import"]))
    source.process_wiki_updates(WikiUpdateRequest(limit=1))
    exported = source.export_data(source="test").model_dump()

    kv = StateKV(tmp_path / "target.sqlite3")
    target = MemoryCoreService(
        kv,
        llm=StubLLMProvider(),
        search=MemorySearchService(kv, settings=ai_settings(tmp_path / "target.sqlite3"), embedding=StubEmbeddingProvider()),
    )
    result = target.import_data(GovernanceImportRequest(payload=exported, source="test"))
    duplicate = target.import_data(GovernanceImportRequest(payload=exported, source="test"))
    search = target.search(SearchRequest(query="searchable memories", mode="keyword", sourceTypes=["memory"], matchMode="any"))
    context = target.context(ContextRequest(query="Stub wiki update", sourceTypes=["wikiPage"], matchMode="any"))

    assert result.schemaVersion == 2
    assert result.imported["projects"] == 1
    assert result.auditId.startswith("aud_")
    assert result.imported["memories"] == 1
    assert result.imported["observations"] == 1
    assert result.imported["wikiPages"] == 1
    assert duplicate.skipped["memories"] == 1
    assert duplicate.skipped["observations"] == 1
    assert target.list_audit()[-1].action == "import"
    assert search.results
    assert context.context


def test_import_rejects_unsupported_schema_version(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))

    with pytest.raises(ValueError, match="unsupported governance schemaVersion"):
        service.import_data(GovernanceImportRequest(payload={"schemaVersion": 999}, source="test"))


def test_forget_deletes_memory_and_writes_audit(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))
    remembered = service.remember(RememberRequest(content="Forget this memory.", language="en"))

    result = service.forget(ForgetRequest(memoryId=remembered.memoryId, reason="incorrect"))

    assert result.memoryId == remembered.memoryId
    assert result.deletedMemory.content == "Forget this memory."
    assert service.list_memories() == []
    assert service.list_audit()[-1].action == "forget"
    assert service.list_audit()[-1].targetId == remembered.memoryId
    assert service.list_audit()[-1].details["reason"] == "incorrect"


def test_forget_missing_memory_does_not_write_success_audit(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))

    with pytest.raises(MemoryNotFoundError):
        service.forget(ForgetRequest(memoryId="mem_missing"))

    assert service.list_audit() == []


def test_wiki_jobs_are_enqueued_and_applied(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())

    observed = service.observe(ObserveRequest(content="Project chooses FastAPI.", language="en"))
    remembered = service.remember(RememberRequest(content="Use FastAPI for backend APIs.", language="en"))
    jobs = service.list_wiki_jobs()

    assert len(jobs) == 2
    assert {source for job in jobs for source in job.sourceIds} == {
        f"observation:{observed.observationId}",
        f"memory:{remembered.memoryId}",
    }

    maintenance = service.run_maintenance(MaintenanceRunRequest(limit=5))
    summary = service.list_summaries()[0]
    assert f"summary:{summary.id}" in {source for job in service.list_wiki_jobs() for source in job.sourceIds}
    assert maintenance.wiki["jobs"]
    assert maintenance.wiki["jobs"][0]["status"] == "applied"
    assert maintenance.wiki["pages"][0]["content"] == "Stub wiki update"
    assert [item["kind"] for item in maintenance.wiki["knowledge"]] == ["semantic", "procedural", "lesson"]
    assert "Stub semantic knowledge" in {item.content for item in service.list_knowledge()}
    assert "Stub crystal digest" not in {item.content for item in service.list_knowledge()}
    page_source_sets = [set(page.sourceIds) for page in service.list_wiki_pages()]
    assert all(
        any(set(job["sourceIds"]).issubset(page_sources) for page_sources in page_source_sets)
        for job in maintenance.wiki["jobs"]
    )
    assert "wiki_update" in [record.action for record in service.list_audit()]


def test_wiki_records_inherit_project_scope_for_viewer_filters(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())

    observed = service.observe(
        ObserveRequest(
            content="Home training prefers 45 minute low impact sessions.",
            project="home-fitness",
            cwd="/tmp/home-fitness",
            language="en",
        ),
    )
    project_id = observed.observation.projectId

    jobs = service.list_wiki_jobs()
    assert jobs[0].project == "home-fitness"
    assert jobs[0].projectId == project_id

    service.run_maintenance(MaintenanceRunRequest(limit=5))

    assert service.list_wiki_pages()
    assert service.list_knowledge()
    assert {page.projectId for page in service.list_wiki_pages()} == {project_id}
    assert {item.projectId for item in service.list_knowledge()} == {project_id}


def test_wiki_processing_failure_preserves_source_data(tmp_path):
    llm = StubLLMProvider()
    llm.update_wiki = lambda *args, **kwargs: "invalid output"  # type: ignore[method-assign]
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=llm)
    remembered = service.remember(RememberRequest(content="Keep this memory after wiki failure.", language="en"))

    result = service.process_wiki_updates()

    assert result.jobs[0].status == "failed"
    assert "invalid wiki update proposal" in (result.jobs[0].lastError or "")
    assert service.list_memories()[0].id == remembered.memoryId
    assert service.list_knowledge()
    assert service.list_wiki_pages() == []


def test_maintenance_retries_failed_wiki_jobs(tmp_path):
    llm = StubLLMProvider()
    llm.update_wiki = lambda *args, **kwargs: "invalid output"  # type: ignore[method-assign]
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=llm)
    service.remember(RememberRequest(content="Maintenance should retry Wiki jobs.", language="en"))
    failed = service.process_wiki_updates()
    assert failed.jobs[0].status == "failed"

    service.llm = StubLLMProvider()
    result = service.run_maintenance(MaintenanceRunRequest(limit=5))

    assert result.errors == []
    assert result.wiki["retried"] == 1
    assert result.wiki["jobs"][0]["status"] == "applied"
    assert service.list_wiki_pages()[0].content == "Stub wiki update"


def test_maintenance_retries_failed_llm_processing(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider(fail=True))
    observed = service.observe(ObserveRequest(content="Retry failed LLM processing.", language="en"))
    assert observed.processingJob is not None
    assert observed.processingJob.status == "pending"

    service.llm = StubLLMProvider()
    result = service.run_maintenance(MaintenanceRunRequest(limit=5))
    jobs = result.llm["jobs"]

    assert jobs[0]["status"] == "done"
    assert jobs[0]["attempts"] == 1
    assert service.list_summaries()[0].content == "Stub summary"
    assert service.list_memory_candidates()


def test_wiki_rebuild_all_creates_jobs_and_pages(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())
    service.remember(RememberRequest(content="Document project overview in Wiki.", language="en"))

    result = service.rebuild_wiki(WikiRebuildRequest(all=True))

    assert len(result.jobs) == 6
    assert all(job.status == "applied" for job in result.jobs)
    assert len(service.list_wiki_pages()) == 6
    knowledge = service.list_knowledge()
    assert len(knowledge) == 3
    assert all(item.fingerprint for item in knowledge)
    semantic = next(item for item in knowledge if item.kind == "semantic")
    assert semantic.kind == "semantic"
    assert semantic.reinforcements == 0


def test_wiki_rebuild_reuses_existing_knowledge(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())
    service.remember(RememberRequest(content="Document project overview in Wiki.", language="en"))

    first = service.rebuild_wiki(WikiRebuildRequest(all=True))
    first_ids = {item.id for item in service.list_knowledge()}
    second = service.rebuild_wiki(WikiRebuildRequest(all=True))
    second_knowledge = service.list_knowledge()

    assert len(first.knowledge) == 3
    assert len(second.knowledge) == 3
    assert {item.id for item in second_knowledge} == first_ids
    assert len(second_knowledge) == 3
    assert {item.kind for item in second_knowledge} == {"semantic", "procedural", "lesson"}


def test_wiki_consolidation_lesson_crystal_reflect_and_lint(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())
    first = service.remember(
        RememberRequest(
            content="When validating AgentMemory, run pytest and OpenSpec validation.",
            language="en",
            concepts=["validation", "workflow"],
        ),
    )
    second = service.remember(
        RememberRequest(
            content="AgentMemory validation workflow should include pytest before archive.",
            language="en",
            concepts=["validation", "workflow"],
        ),
    )

    consolidated = service.consolidate_wiki(WikiConsolidateRequest(limit=10, minEvidence=2))
    lesson = service.file_wiki_answer(
        WikiFileAnswerRequest(
            query="How should validation run?",
            content="Always run pytest and OpenSpec validation before archiving changes.",
            kind="lesson",
            sourceIds=[f"memory:{first.memoryId}", f"memory:{second.memoryId}"],
            concepts=["validation"],
            confidence=0.8,
        ),
    ).record
    recalled = service.recall_lessons(LessonRecallRequest(query="pytest validation"))
    crystal = service.create_crystal(
        CrystalCreateRequest(sourceIds=[f"memory:{first.memoryId}", f"memory:{second.memoryId}"]),
    )
    reflected = service.reflect_wiki(WikiReflectRequest(limit=20))
    lint = service.lint_wiki()

    assert consolidated.semantic
    assert consolidated.procedural
    assert lesson.kind == "lesson"
    assert recalled.lessons[0].id == lesson.id
    assert crystal.crystal.kind == "crystal"
    assert crystal.lessons
    assert reflected.insights
    assert all(issue.type != "missing_source" for issue in lint.issues)


def test_llm_consolidation_creates_dynamic_page_and_lint_issue(tmp_path):
    kv = StateKV(tmp_path / "memory.sqlite3")
    search = MemorySearchService(
        kv,
        settings=ai_settings(tmp_path / "memory.sqlite3"),
        embedding=StubEmbeddingProvider(),
        llm=StubLLMProvider(),
    )
    service = MemoryCoreService(kv, llm=StubLLMProvider(), search=search)
    service.remember(RememberRequest(content="LLM Wiki consolidation should create dynamic concept pages.", concepts=["wiki"]))
    service.remember(RememberRequest(content="LLM Wiki consolidation should detect stale claims.", concepts=["wiki"]))

    consolidated = service.consolidate_wiki(WikiConsolidateRequest(limit=10, minEvidence=2))
    lint = service.lint_wiki()
    search_result = service.search(
        SearchRequest(query="llm-wiki-consolidation concept", mode="hybrid", sourceTypes=["wikiPage"]),
    )

    assert consolidated.pages
    assert consolidated.pages[0].type == "concept"
    assert consolidated.pages[0].slug == "llm-wiki-consolidation"
    assert consolidated.pages[0].parentTopic == "project_overview"
    assert consolidated.lintIssues[0].type == "stale"
    assert any(issue.type == "contradiction" for issue in lint.issues)
    assert search_result.results
    assert search_result.results[0].sourceId == consolidated.pages[0].id


def test_query_filed_insight_is_searchable_and_contextual(tmp_path):
    kv = StateKV(tmp_path / "memory.sqlite3")
    search = MemorySearchService(
        kv,
        settings=ai_settings(tmp_path / "memory.sqlite3"),
        embedding=StubEmbeddingProvider(),
        llm=StubLLMProvider(),
    )
    service = MemoryCoreService(kv, llm=StubLLMProvider(), search=search)

    filed = service.file_wiki_answer(
        WikiFileAnswerRequest(
            query="What is LLM Wiki?",
            content="LLM Wiki means structured compounding knowledge rather than fixed pages.",
            kind="insight",
            concepts=["wiki", "llm"],
            confidence=0.9,
        ),
    )
    service.search_service.process_pending()
    result = service.search(SearchRequest(query="compounding knowledge", mode="hybrid", sourceTypes=["insight"]))
    context = service.context(ContextRequest(query="LLM Wiki compounding", sourceTypes=["insight"]))

    assert filed.record.id.startswith("ins_")
    assert result.results[0].sourceType == "insight"
    assert context.evidence[0]["sourceType"] == "insight"
