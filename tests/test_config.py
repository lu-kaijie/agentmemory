from agentmemory.config import Settings


def test_default_configuration_loads(tmp_path):
    settings = Settings(db_path=tmp_path / "agentmemory.sqlite3")

    assert settings.host == "127.0.0.1"
    assert settings.port == 3111
    assert settings.log_level == "INFO"
    assert str(settings.db_path).endswith("agentmemory.sqlite3")


def test_secret_is_redacted(tmp_path):
    settings = Settings(
        db_path=tmp_path / "db.sqlite3",
        secret="super-secret",
        llm_base_url="https://llm.example/v1",
        llm_api_key="llm-secret",
        llm_model="llm-model",
        embedding_base_url="https://embedding.example/v1",
        embedding_api_key="embedding-secret",
        embedding_model="embedding-model",
    )

    summary = settings.safe_summary()

    assert summary["secret_configured"] is True
    assert summary["secret"] == "<redacted>"
    assert "super-secret" not in str(summary)
    assert summary["llm"]["api_key_configured"] is True
    assert summary["embedding"]["api_key_configured"] is True
    assert "llm-secret" not in str(summary)
    assert "embedding-secret" not in str(summary)


def test_missing_ai_settings_are_reported(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    settings = Settings(db_path=tmp_path / "db.sqlite3")

    assert settings.missing_ai_settings() == [
        "AGENTMEMORY_LLM_BASE_URL",
        "AGENTMEMORY_LLM_API_KEY",
        "AGENTMEMORY_LLM_MODEL",
        "AGENTMEMORY_EMBEDDING_BASE_URL",
        "AGENTMEMORY_EMBEDDING_API_KEY",
        "AGENTMEMORY_EMBEDDING_MODEL",
    ]


def test_complete_ai_settings_are_valid(tmp_path):
    settings = Settings(
        db_path=tmp_path / "db.sqlite3",
        llm_base_url="https://llm.example/v1",
        llm_api_key="llm-key",
        llm_model="llm-model",
        embedding_base_url="https://embedding.example/v1",
        embedding_api_key="embedding-key",
        embedding_model="embedding-model",
    )

    assert settings.missing_ai_settings() == []
