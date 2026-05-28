from fastapi.testclient import TestClient

from agentmemory.api import create_app
from agentmemory.config import Settings
from agentmemory.providers import MissingAIProviderSettings
from conftest import ai_settings


def test_livez_endpoint(tmp_path):
    app = create_app(ai_settings(tmp_path / "health.sqlite3"))
    client = TestClient(app)

    response = client.get("/agentmemory/livez")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_health_endpoint_reports_database_and_redacts_secret(tmp_path):
    settings = ai_settings(tmp_path / "health.sqlite3")
    settings.secret = "secret-value"
    settings.llm_api_key = "secret-llm-key"
    settings.embedding_api_key = "secret-embedding-key"
    app = create_app(settings)
    client = TestClient(app)

    response = client.get("/agentmemory/health")
    body = response.json()

    assert response.status_code == 200
    assert body["service"] == "agentmemory"
    assert body["status"] == "ok"
    assert body["database"]["ok"] is True
    assert body["providers"]["llm"]["provider"] == "openai-compatible"
    assert body["providers"]["llm"]["ready"] is True
    assert body["providers"]["embedding"]["provider"] == "openai-compatible"
    assert body["providers"]["embedding"]["ready"] is True
    assert body["config"]["secret"] == "<redacted>"
    assert "secret-value" not in str(body)
    assert "secret-llm-key" not in str(body)
    assert "secret-embedding-key" not in str(body)


def test_create_app_requires_ai_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    try:
        create_app(Settings(db_path=tmp_path / "missing.sqlite3"))
    except MissingAIProviderSettings as exc:
        assert "AGENTMEMORY_LLM_BASE_URL" in exc.missing_settings
        assert "AGENTMEMORY_EMBEDDING_API_KEY" in exc.missing_settings
    else:  # pragma: no cover - assertion path
        raise AssertionError("create_app should fail when AI settings are missing")
