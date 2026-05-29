from fastapi.testclient import TestClient

from agentmemory.api import create_app
from conftest import StubLLMProvider, ai_settings


def test_rest_observe_remember_and_list_endpoints(tmp_path):
    app = create_app(ai_settings(tmp_path / "api.sqlite3"))
    app.state.providers = type("Providers", (), {"llm": StubLLMProvider(), "health_summary": lambda _self: {}})()
    app.state.memory_core.llm = app.state.providers.llm
    client = TestClient(app)

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

    assert observe.status_code == 200
    assert observe.json()["sessionId"] == "ses_api"
    assert observe.json()["processingJob"]["status"] == "done"
    assert observe.json()["summary"]["content"] == "Stub summary"
    assert len(observe.json()["memoryCandidates"]) == 1
    assert remember.status_code == 200
    assert remember.json()["memoryId"].startswith("mem_")
    assert sessions.json()["sessions"][0]["observationCount"] == 1
    assert memories.json()["memories"][0]["content"] == "Memory core does not perform RAG indexing."
    assert [item["action"] for item in audit.json()["audit"]] == ["observe", "llm_processing_done", "remember"]
    assert summaries.json()["summaries"][0]["content"] == "Stub summary"
    assert candidates.json()["memoryCandidates"][0]["status"] == "candidate"
    assert jobs.json()["llmProcessingJobs"][0]["status"] == "done"
