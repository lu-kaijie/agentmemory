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


def test_viewer_endpoint_returns_html_and_health_stays_json(tmp_path):
    app = create_app(ai_settings(tmp_path / "viewer.sqlite3"))
    client = TestClient(app)

    viewer = client.get("/agentmemory/")
    health = client.get("/agentmemory/health")

    assert viewer.status_code == 200
    assert "text/html" in viewer.headers["content-type"]
    assert "<title>AgentMemory Viewer</title>" in viewer.text
    assert 'id="root"' in viewer.text
    assert "/agentmemory/assets/" in viewer.text
    assert health.status_code == 200
    assert health.headers["content-type"].startswith("application/json")
    assert health.json()["service"] == "agentmemory"


def test_viewer_static_content_has_required_sections_and_no_unsupported_actions():
    from importlib import resources

    html = resources.files("agentmemory.viewer").joinpath("dist/index.html").read_text(encoding="utf-8")
    js_text = "\n".join(
        item.read_text(encoding="utf-8")
        for item in resources.files("agentmemory.viewer").joinpath("dist/assets").iterdir()
        if item.name.endswith(".js")
    )

    required = [
        "AgentMemory Viewer",
        "/agentmemory/assets/",
    ]
    required_js = [
        "/agentmemory/health",
        "/agentmemory/index/status",
        "/agentmemory/projects",
        "/agentmemory/pins",
        "/agentmemory/memories",
        "/agentmemory/summaries",
        "/agentmemory/wiki/pages",
        "/agentmemory/wiki/jobs",
        "/agentmemory/wiki/knowledge",
        "/agentmemory/memory-candidates",
        "/agentmemory/llm-processing-jobs",
        "/agentmemory/audit",
        "/agentmemory/search",
        "/agentmemory/smart-search",
        "/agentmemory/context",
        "/agentmemory/maintenance/run",
        "Run Maintenance",
        "Global",
        "Project",
        "Knowledge",
        "Graph",
        "No graph records yet.",
    ]
    for phrase in required:
        assert phrase in html
    for phrase in required_js:
        assert phrase in js_text

    forbidden = [
        "agentmemory delete",
        "agentmemory export",
        "agentmemory context",
        "/agentmemory/wiki/update",
        "/agentmemory/wiki/rebuild",
        "/agentmemory/export",
        "/agentmemory/delete",
        "edit wiki",
        "delete wiki",
    ]
    for phrase in forbidden:
        assert phrase not in js_text


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
