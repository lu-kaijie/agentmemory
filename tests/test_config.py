from agentmemory.config import Settings


def test_default_configuration_loads(tmp_path):
    settings = Settings(db_path=tmp_path / "agentmemory.sqlite3")

    assert settings.host == "127.0.0.1"
    assert settings.port == 3111
    assert settings.log_level == "INFO"
    assert str(settings.db_path).endswith("agentmemory.sqlite3")


def test_secret_is_redacted(tmp_path):
    settings = Settings(db_path=tmp_path / "db.sqlite3", secret="super-secret")

    summary = settings.safe_summary()

    assert summary["secret_configured"] is True
    assert summary["secret"] == "<redacted>"
    assert "super-secret" not in str(summary)

