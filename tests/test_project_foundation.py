from pathlib import Path

from agentmemory.config import Settings


def test_env_example_and_scripts_document_local_development():
    root = Path(__file__).resolve().parents[1]
    env_example = (root / ".env.example").read_text(encoding="utf-8")
    dev_script = root / "scripts" / "dev.sh"
    test_script = root / "scripts" / "test.sh"

    assert "AGENTMEMORY_DB_PATH" in env_example
    assert "AGENTMEMORY_VECTOR_DB_PATH" in env_example
    assert "AGENTMEMORY_LLM_BASE_URL" in env_example
    assert "AGENTMEMORY_EMBEDDING_BASE_URL" in env_example
    assert "AGENTMEMORY_MAINTENANCE_LIMIT" in env_example
    assert "AGENTMEMORY_REST_ENVELOPE" in env_example
    assert "uv run agentmemory serve" in dev_script.read_text(encoding="utf-8")
    assert "uv run pytest" in test_script.read_text(encoding="utf-8")
    assert "uv run openspec validate --all --strict" in test_script.read_text(encoding="utf-8")


def test_maintenance_settings_are_visible_without_secrets(tmp_path):
    settings = Settings(
        db_path=tmp_path / "memory.sqlite3",
        maintenance_limit=7,
        rest_envelope=True,
        llm_api_key="secret-llm",
        embedding_api_key="secret-embedding",
    )

    summary = settings.safe_summary()

    assert summary["maintenance"] == {"limit": 7}
    assert summary["rest"] == {"envelope": True}
    assert "secret-llm" not in str(summary)
    assert "secret-embedding" not in str(summary)
