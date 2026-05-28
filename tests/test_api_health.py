from fastapi.testclient import TestClient

from agentmemory.api import create_app
from agentmemory.config import Settings


def test_livez_endpoint(tmp_path):
    app = create_app(Settings(db_path=tmp_path / "health.sqlite3"))
    client = TestClient(app)

    response = client.get("/agentmemory/livez")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_health_endpoint_reports_database_and_redacts_secret(tmp_path):
    app = create_app(Settings(db_path=tmp_path / "health.sqlite3", secret="secret-value"))
    client = TestClient(app)

    response = client.get("/agentmemory/health")
    body = response.json()

    assert response.status_code == 200
    assert body["service"] == "agentmemory"
    assert body["status"] == "ok"
    assert body["database"]["ok"] is True
    assert body["config"]["secret"] == "<redacted>"
    assert "secret-value" not in str(body)

