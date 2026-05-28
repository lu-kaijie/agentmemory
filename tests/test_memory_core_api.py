from fastapi.testclient import TestClient

from agentmemory.api import create_app
from conftest import ai_settings


def test_rest_observe_remember_and_list_endpoints(tmp_path):
    app = create_app(ai_settings(tmp_path / "api.sqlite3"))
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

    assert observe.status_code == 200
    assert observe.json()["sessionId"] == "ses_api"
    assert remember.status_code == 200
    assert remember.json()["memoryId"].startswith("mem_")
    assert sessions.json()["sessions"][0]["observationCount"] == 1
    assert memories.json()["memories"][0]["content"] == "Memory core does not perform RAG indexing."
    assert [item["action"] for item in audit.json()["audit"]] == ["observe", "remember"]
