from fastapi.testclient import TestClient

from agentmemory.api import create_app
from conftest import StubEmbeddingProvider, StubLLMProvider, ai_settings


def test_rest_observe_remember_and_list_endpoints(tmp_path):
    app = create_app(ai_settings(tmp_path / "api.sqlite3"))
    app.state.providers = type(
        "Providers",
        (),
        {
            "llm": StubLLMProvider(),
            "embedding": StubEmbeddingProvider(),
            "health_summary": lambda _self: {},
        },
    )()
    app.state.memory_core.llm = app.state.providers.llm
    app.state.search_service.embedding = app.state.providers.embedding
    app.state.search_service.llm = app.state.providers.llm
    client = TestClient(app)

    session_start = client.post(
        "/agentmemory/session/start",
        json={"sessionId": "ses_api", "project": "agentmemory", "cwd": str(tmp_path)},
    )
    observe = client.post(
        "/agentmemory/observe",
        json={
            "sessionId": "ses_api",
            "content": "Implemented the REST memory core endpoints.",
            "type": "work-summary",
            "project": "agentmemory",
            "language": "en",
        },
    )
    session_end = client.post(
        "/agentmemory/session/end",
        json={
            "sessionId": "ses_api",
            "content": "Finished REST lifecycle acceptance.",
            "language": "en",
        },
    )
    remember = client.post(
        "/agentmemory/remember",
        json={
            "content": "Memory core does not perform RAG indexing.",
            "type": "decision",
            "concepts": ["memory-core"],
            "language": "en",
        },
    )

    sessions = client.get("/agentmemory/sessions")
    memories = client.get("/agentmemory/memories")
    audit = client.get("/agentmemory/audit")
    summaries = client.get("/agentmemory/summaries")
    candidates = client.get("/agentmemory/memory-candidates")
    jobs = client.get("/agentmemory/llm-processing-jobs")
    search = client.post("/agentmemory/search", json={"query": "RAG indexing", "mode": "keyword", "matchMode": "any"})
    smart = client.post("/agentmemory/smart-search", json={"query": "REST memory", "mode": "hybrid"})
    context = client.post("/agentmemory/context", json={"query": "REST memory", "sourceTypes": ["memory"]})
    index_status = client.get("/agentmemory/index/status")
    index_repair = client.post("/agentmemory/index/repair")
    index_rebuild = client.post("/agentmemory/index/rebuild")
    exported = client.get("/agentmemory/export")
    wiki_jobs = client.get("/agentmemory/wiki/jobs")
    wiki_update = client.post("/agentmemory/wiki/update", json={"limit": 1})
    wiki_pages = client.get("/agentmemory/wiki/pages")

    assert session_start.status_code == 200
    assert session_start.json()["session"]["status"] == "active"
    assert observe.status_code == 200
    assert observe.json()["sessionId"] == "ses_api"
    assert observe.json()["processingJob"]["status"] == "done"
    assert observe.json()["summary"]["content"] == "Stub summary"
    assert len(observe.json()["memoryCandidates"]) == 1
    assert session_end.status_code == 200
    assert session_end.json()["session"]["status"] == "ended"
    assert session_end.json()["summary"]["kind"] == "session"
    assert remember.status_code == 200
    assert remember.json()["memoryId"].startswith("mem_")
    assert sessions.json()["sessions"][0]["observationCount"] == 1
    assert sessions.json()["sessions"][0]["summaryId"] == session_end.json()["summary"]["id"]
    assert memories.json()["memories"][0]["content"] == "Memory core does not perform RAG indexing."
    assert [item["action"] for item in audit.json()["audit"]] == [
        "session_start",
        "observe",
        "llm_processing_done",
        "session_end",
        "remember",
    ]
    assert summaries.json()["summaries"][0]["content"] == "Stub summary"
    assert candidates.json()["memoryCandidates"][0]["status"] == "candidate"
    assert jobs.json()["llmProcessingJobs"][0]["status"] == "done"
    assert search.status_code == 200
    assert search.json()["results"]
    assert smart.status_code == 200
    assert smart.json()["answer"] == "stub explanation"
    assert smart.json()["evidence"]
    assert context.status_code == 200
    assert context.json()["context"]
    assert context.json()["evidence"][0]["sourceType"] == "memory"
    assert context.json()["confidence"] > 0
    assert index_status.status_code == 200
    assert index_status.json()["documents"] >= 2
    assert index_repair.status_code == 200
    assert index_rebuild.status_code == 200
    assert exported.status_code == 200
    assert exported.json()["memories"][0]["content"] == "Memory core does not perform RAG indexing."
    assert exported.json()["audit"][-1]["action"] == "export"
    assert wiki_jobs.status_code == 200
    assert wiki_jobs.json()["wikiUpdateJobs"]
    assert wiki_update.status_code == 200
    assert wiki_update.json()["jobs"][0]["status"] == "applied"
    assert wiki_pages.status_code == 200
    assert wiki_pages.json()["wikiPages"][0]["content"] == "Stub wiki update"


def test_rest_export_redacts_secrets_and_forget_memory(tmp_path):
    settings = ai_settings(tmp_path / "governance.sqlite3")
    settings.secret = "rest-secret"
    settings.llm_api_key = "llm-secret"
    settings.embedding_api_key = "embedding-secret"
    app = create_app(settings)
    app.state.providers = type(
        "Providers",
        (),
        {
            "llm": StubLLMProvider(),
            "embedding": StubEmbeddingProvider(),
            "health_summary": lambda _self: {},
        },
    )()
    app.state.memory_core.llm = app.state.providers.llm
    app.state.search_service.embedding = app.state.providers.embedding
    app.state.search_service.llm = app.state.providers.llm
    client = TestClient(app)

    remember = client.post(
        "/agentmemory/remember",
        json={"content": "REST forget removes this memory.", "language": "en"},
    )
    memory_id = remember.json()["memoryId"]
    app.state.search_service.process_pending()

    exported = client.get("/agentmemory/export")
    forget = client.post("/agentmemory/forget", json={"memoryId": memory_id, "reason": "api test"})
    missing = client.post("/agentmemory/forget", json={"memoryId": memory_id})
    memories = client.get("/agentmemory/memories")
    search = client.post("/agentmemory/search", json={"query": "REST forget", "mode": "hybrid"})
    audit = client.get("/agentmemory/audit")
    exported_text = exported.text

    assert exported.status_code == 200
    assert "llm-secret" not in exported_text
    assert "embedding-secret" not in exported_text
    assert "rest-secret" not in exported_text
    assert forget.status_code == 200
    assert forget.json()["memoryId"] == memory_id
    assert forget.json()["auditId"].startswith("aud_")
    assert missing.status_code == 404
    assert missing.json()["detail"]["error"] == "memory_not_found"
    assert memories.json()["memories"] == []
    assert search.json()["results"] == []
    assert [item["action"] for item in audit.json()["audit"]] == ["remember", "export", "forget"]


def test_rest_wiki_rebuild(tmp_path):
    app = create_app(ai_settings(tmp_path / "wiki-api.sqlite3"))
    app.state.providers = type(
        "Providers",
        (),
        {
            "llm": StubLLMProvider(),
            "embedding": StubEmbeddingProvider(),
            "health_summary": lambda _self: {},
        },
    )()
    app.state.memory_core.llm = app.state.providers.llm
    app.state.search_service.embedding = app.state.providers.embedding
    app.state.search_service.llm = app.state.providers.llm
    client = TestClient(app)

    client.post("/agentmemory/remember", json={"content": "REST Wiki rebuild evidence.", "language": "en"})
    rebuild = client.post("/agentmemory/wiki/rebuild", json={"all": True})
    pages = client.get("/agentmemory/wiki/pages")
    knowledge = client.get("/agentmemory/wiki/knowledge")
    jobs = client.get("/agentmemory/wiki/jobs")

    assert rebuild.status_code == 200
    assert len(rebuild.json()["jobs"]) == 6
    assert all(job["status"] == "applied" for job in rebuild.json()["jobs"])
    assert len(pages.json()["wikiPages"]) == 6
    knowledge_items = knowledge.json()["knowledge"]
    assert len(knowledge_items) == 4
    assert all(item["fingerprint"] for item in knowledge_items)
    assert jobs.json()["wikiUpdateJobs"]
