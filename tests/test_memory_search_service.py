from agentmemory.config import Settings
from agentmemory.core.models import (
    ContextRequest,
    ForgetRequest,
    ObserveRequest,
    RememberRequest,
    SearchRequest,
    SmartSearchRequest,
    WikiRebuildRequest,
)
from agentmemory.core.search import MemorySearchService
from agentmemory.core.service import MemoryCoreService
from agentmemory.state import StateKV
from conftest import StubEmbeddingProvider, StubLLMProvider


def _settings(tmp_path):
    return Settings(
        db_path=tmp_path / "memory.sqlite3",
        vector_db_path=tmp_path / "vector",
        vector_table="test_vectors",
        llm_base_url="https://api.openai.com/v1",
        llm_api_key="test-llm-key",
        llm_model="gpt-test",
        embedding_base_url="https://api.openai.com/v1",
        embedding_api_key="test-embedding-key",
        embedding_model="text-embedding-test",
    )


def _service(tmp_path, embedding=None, llm=None):
    settings = _settings(tmp_path)
    kv = StateKV(settings.db_path)
    search = MemorySearchService(
        kv,
        settings=settings,
        embedding=embedding or StubEmbeddingProvider(),
        llm=llm or StubLLMProvider(),
    )
    return MemoryCoreService(kv, llm=llm or StubLLMProvider(), search=search)


def test_indexing_on_observe_summary_and_remember(tmp_path):
    service = _service(tmp_path)

    observed = service.observe(
        ObserveRequest(
            sessionId="ses_search",
            content="FastAPI search indexing should cover observations.",
            language="en",
            project="agentmemory",
            concepts=["search"],
        ),
    )
    remembered = service.remember(
        RememberRequest(
            content="Memory search uses FTS5 and LanceDB.",
            language="en",
            concepts=["search", "lancedb"],
        ),
    )

    status = service.index_status()
    assert observed.summary is not None
    assert remembered.memoryId.startswith("mem_")
    assert status.documents == 3
    assert status.fts5["documents"] == 3
    assert status.failedJobs == 0
    jobs = service.search_service.process_pending()
    assert len(jobs) == 3
    assert all(job.status == "done" for job in jobs)


def test_write_enqueues_embedding_without_blocking_keyword_search(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(fail=True))

    result = service.remember(
        RememberRequest(
            content="Keyword search is available before vector indexing finishes.",
            language="en",
        ),
    )

    status = service.index_status()
    keyword = service.search(SearchRequest(query="Keyword", mode="keyword"))
    vector = service.search(SearchRequest(query="semantic", mode="vector"))

    assert result.memoryId.startswith("mem_")
    assert status.documents == 1
    assert status.failedJobs == 0
    assert keyword.results
    assert vector.results == []


def test_keyword_search_finds_indexed_memory(tmp_path):
    service = _service(tmp_path)
    service.remember(
        RememberRequest(
            content="FastAPI was selected for the backend service.",
            language="en",
            concepts=["backend"],
        ),
    )

    result = service.search(SearchRequest(query="FastAPI", mode="keyword"))

    assert result.mode == "keyword"
    assert result.results
    assert result.results[0].sourceType == "memory"
    assert "FastAPI" in result.results[0].content
    assert result.results[0].matchSources == ["keyword"]


def test_vector_and_hybrid_search_preserve_evidence(tmp_path):
    service = _service(tmp_path)
    service.remember(
        RememberRequest(
            content="RAG search combines keyword and semantic retrieval.",
            language="en",
            concepts=["rag", "search"],
        ),
    )
    service.search_service.process_pending()

    vector = service.search(SearchRequest(query="semantic memory retrieval", mode="vector"))
    hybrid = service.search(SearchRequest(query="RAG search", mode="hybrid"))

    assert vector.results
    assert "vector" in vector.results[0].matchSources
    assert hybrid.results
    assert hybrid.results[0].sourceId == vector.results[0].sourceId
    assert set(hybrid.results[0].matchSources) == {"keyword", "vector"}


def test_smart_search_uses_llm_explanation_and_evidence(tmp_path):
    service = _service(tmp_path, llm=StubLLMProvider())
    service.remember(
        RememberRequest(
            content="LLM search explanations must cite evidence.",
            language="en",
            concepts=["llm", "evidence"],
        ),
    )

    result = service.smart_search(SmartSearchRequest(query="How should search explain results?"))

    assert result.answer == "stub explanation"
    assert result.results
    assert result.evidence[0]["sourceId"] == result.results[0].sourceId
    assert result.context


def test_no_results_smart_search_response(tmp_path):
    service = _service(tmp_path)

    result = service.smart_search(SmartSearchRequest(query="missing", mode="keyword"))

    assert result.results == []
    assert result.evidence == []
    assert "未找到" in result.answer


def test_index_failure_preserves_source_data(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(fail=True))

    result = service.remember(
        RememberRequest(
            content="Source data survives embedding failure.",
            language="en",
        ),
    )
    service.search_service.process_pending()

    memories = service.list_memories()
    status = service.index_status()
    search = service.search(SearchRequest(query="Source", mode="keyword"))

    assert memories[0].id == result.memoryId
    assert status.failedJobs == 1
    assert search.results


def test_rebuild_and_repair(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(fail=True))
    service.remember(RememberRequest(content="Repair retries failed search indexes.", language="en"))
    service.search_service.process_pending()
    assert service.index_status().failedJobs == 1

    service.search_service.embedding = StubEmbeddingProvider()
    repair = service.index_repair()
    rebuild = service.index_rebuild()

    assert repair["documents"] == 1
    assert rebuild["documents"] == 1
    assert service.index_status().failedJobs == 0


def test_vector_search_recovers_from_stale_dimension_table(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider())
    service.remember(RememberRequest(content="Search should recover stale vector dimensions.", language="en"))
    service.search_service.process_pending()
    assert service.search(SearchRequest(query="semantic search", mode="vector")).results

    service.search_service._drop_vector_table()
    service.search_service._table([0.1, 0.2])

    result = service.search(SearchRequest(query="semantic search", mode="vector"))

    assert result.results
    assert service.index_status().failedJobs == 0


def test_forget_removes_memory_from_keyword_vector_and_hybrid_search(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider())
    remembered = service.remember(
        RememberRequest(
            content="Governance forget removes searchable memory evidence.",
            language="en",
            concepts=["governance", "search"],
        ),
    )
    service.search_service.process_pending()

    assert service.search(SearchRequest(query="Governance", mode="keyword")).results
    assert service.search(SearchRequest(query="searchable memory evidence", mode="vector")).results
    assert service.search(SearchRequest(query="Governance memory", mode="hybrid")).results

    service.forget(ForgetRequest(memoryId=remembered.memoryId, reason="test cleanup"))

    assert service.list_memories() == []
    assert service.search(SearchRequest(query="Governance", mode="keyword")).results == []
    assert service.search(SearchRequest(query="searchable memory evidence", mode="vector")).results == []
    assert service.search(SearchRequest(query="Governance memory", mode="hybrid")).results == []


def test_wiki_pages_are_indexed_and_searchable(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(), llm=StubLLMProvider())
    service.remember(RememberRequest(content="Wiki search should find durable project knowledge.", language="en"))

    service.rebuild_wiki(WikiRebuildRequest(topic="technical_decisions"))
    service.search_service.process_pending()

    keyword = service.search(SearchRequest(query="Stub wiki", mode="keyword", sourceTypes=["wikiPage"]))
    vector = service.search(SearchRequest(query="durable project knowledge", mode="vector", sourceTypes=["wikiPage"]))
    hybrid = service.search(SearchRequest(query="Stub wiki knowledge", mode="hybrid", sourceTypes=["wikiPage"]))

    assert keyword.results
    assert keyword.results[0].sourceType == "wikiPage"
    assert vector.results
    assert vector.results[0].sourceType == "wikiPage"
    assert hybrid.results
    assert {result.sourceType for result in hybrid.results} == {"wikiPage"}


def test_distilled_knowledge_is_indexed_and_searchable(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(), llm=StubLLMProvider())
    service.remember(RememberRequest(content="Wiki should distill durable knowledge records.", language="en"))

    result = service.process_wiki_updates()
    service.search_service.process_pending()

    assert {item.kind for item in result.knowledge} == {"semantic", "procedural", "lesson", "crystal"}
    search = service.search(SearchRequest(query="semantic knowledge", mode="hybrid", sourceTypes=["knowledge"]))
    assert search.results
    assert {item.sourceType for item in search.results} == {"knowledge"}


def test_context_uses_default_durable_sources_and_groups_results(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(), llm=StubLLMProvider())
    service.observe(ObserveRequest(sessionId="ses_context", content="Observation should not be default context.", language="en"))
    service.remember(RememberRequest(content="Memory context should include durable project decisions.", language="en"))
    service.process_wiki_updates()
    service.search_service.process_pending()

    result = service.context(ContextRequest(query="memory context durable project", limit=10))

    assert result.context.startswith("AgentMemory context:")
    assert result.evidence
    assert result.confidence > 0
    assert result.compressed is False
    assert result.knowledge
    assert result.wikiPages
    assert result.memories
    assert "observation" not in {item["sourceType"] for item in result.evidence}
    first_source = result.evidence[0]["sourceType"]
    assert first_source in {"knowledge", "wikiPage"}
    assert f"[{first_source}:{result.evidence[0]['sourceId']}]" in result.context


def test_context_honors_source_type_project_and_language_filters(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(), llm=StubLLMProvider())
    service.observe(
        ObserveRequest(
            sessionId="ses_context_filter",
            content="Filtered observation context evidence.",
            language="en",
            project="agentmemory",
        ),
    )

    result = service.context(
        ContextRequest(
            query="Filtered observation",
            sourceTypes=["observation"],
            project="agentmemory",
            language="en",
        ),
    )
    wrong_project = service.context(
        ContextRequest(query="Filtered observation", sourceTypes=["observation"], project="other"),
    )

    assert result.evidence
    assert {item["sourceType"] for item in result.evidence} == {"observation"}
    assert result.memories[0].sourceType == "observation"
    assert wrong_project.context == ""
    assert wrong_project.confidence == 0


def test_context_compresses_or_truncates_when_over_budget(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(), llm=StubLLMProvider())
    service.remember(RememberRequest(content="Memory " + ("context " * 80), language="en"))

    compressed = service.context(ContextRequest(query="Memory context", tokenBudget=100))
    service.search_service.llm = None
    truncated = service.context(ContextRequest(query="Memory context", tokenBudget=100))

    assert compressed.compressed is True
    assert compressed.context == "stub context"
    assert compressed.evidence
    assert truncated.compressed is False
    assert "[truncated]" in truncated.context
    assert truncated.evidence


def test_context_no_evidence_response(tmp_path):
    service = _service(tmp_path)

    result = service.context(ContextRequest(query="missing", sourceTypes=["memory"]))

    assert result.context == ""
    assert result.evidence == []
    assert result.wikiPages == []
    assert result.knowledge == []
    assert result.memories == []
    assert result.confidence == 0
    assert result.compressed is False
