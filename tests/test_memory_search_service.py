from agentmemory.config import Settings
from agentmemory.core.models import (
    ObserveRequest,
    RememberRequest,
    SearchRequest,
    SmartSearchRequest,
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

    memories = service.list_memories()
    status = service.index_status()
    search = service.search(SearchRequest(query="Source", mode="keyword"))

    assert memories[0].id == result.memoryId
    assert status.failedJobs == 1
    assert search.results


def test_rebuild_and_repair(tmp_path):
    service = _service(tmp_path, embedding=StubEmbeddingProvider(fail=True))
    service.remember(RememberRequest(content="Repair retries failed search indexes.", language="en"))
    assert service.index_status().failedJobs == 1

    service.search_service.embedding = StubEmbeddingProvider()
    repair = service.index_repair()
    rebuild = service.index_rebuild()

    assert repair["documents"] == 1
    assert rebuild["documents"] == 1
    assert service.index_status().failedJobs == 1
