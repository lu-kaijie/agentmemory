import pytest

from agentmemory.core.models import ForgetRequest, ObserveRequest, RememberRequest
from agentmemory.core.service import MemoryCoreService, MemoryNotFoundError
from agentmemory.state import StateKV
from conftest import StubLLMProvider


def test_observe_creates_and_updates_session(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())

    first = service.observe(
        ObserveRequest(
            sessionId="ses_test",
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
            sessionId="ses_test",
            content="Added memory core design notes.",
            project="agentmemory",
            cwd="/repo",
            language="en",
        ),
    )

    sessions = service.list_sessions()
    audit = service.list_audit()

    assert first.sessionId == "ses_test"
    assert second.sessionId == "ses_test"
    assert len(sessions) == 1
    assert sessions[0].observationCount == 2
    assert sessions[0].updatedAt >= sessions[0].startedAt
    assert [record.action for record in audit] == [
        "observe",
        "llm_processing_done",
        "observe",
        "llm_processing_done",
    ]
    assert first.summary is not None
    assert first.processingJob is not None
    assert first.processingJob.status == "done"
    assert len(first.memoryCandidates) == 1


def test_observe_saves_summary_candidates_and_job_without_auto_remember(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider())

    result = service.observe(
        ObserveRequest(
            sessionId="ses_processing",
            content="CLI local writes must require AI settings.",
            language="en",
        ),
    )

    summaries = service.list_summaries()
    candidates = service.list_memory_candidates()
    jobs = service.list_llm_processing_jobs()
    memories = service.list_memories()

    assert result.summary is not None
    assert result.summary.content == "Stub summary"
    assert result.processingJob is not None
    assert result.processingJob.status == "done"
    assert len(result.memoryCandidates) == 1
    assert summaries[0].id == result.summary.id
    assert candidates[0].content == "Remember the tested memory processing behavior."
    assert jobs[0].summaryId == result.summary.id
    assert jobs[0].candidateIds == [candidates[0].id]
    assert memories == []


def test_observe_preserves_observation_when_llm_processing_fails(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"), llm=StubLLMProvider(fail=True))

    result = service.observe(
        ObserveRequest(
            sessionId="ses_failed",
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
    assert result.processingJob.status == "failed"
    assert result.summary is None
    assert result.memoryCandidates == []
    assert jobs[0].status == "failed"
    assert "stub llm failure" in (jobs[0].lastError or "")
    assert summaries == []
    assert candidates == []
    assert audit[-1].action == "llm_processing_failed"


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
    service.observe(ObserveRequest(sessionId="ses_export", content="Export should include observations.", language="en"))
    service.remember(RememberRequest(content="Export should include memories.", language="en"))

    exported = service.export_data(source="test")

    assert exported.version
    assert exported.exportedAt
    assert len(exported.sessions) == 1
    assert len(exported.observations) == 1
    assert len(exported.memories) == 1
    assert len(exported.summaries) == 1
    assert len(exported.memoryCandidates) == 1
    assert len(exported.llmProcessingJobs) == 1
    assert exported.audit[-1].action == "export"
    assert exported.audit[-1].targetType == "governance"
    assert exported.audit[-1].details["memories"] == 1


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
