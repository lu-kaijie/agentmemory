import json

from typer.testing import CliRunner

import agentmemory.cli as cli_module
from agentmemory.cli import app
from conftest import StubLLMProvider


class _StubProviderBundle:
    llm = StubLLMProvider()

    def health_summary(self):
        return {
            "llm": {
                "provider": "openai-compatible",
                "model": "gpt-test",
                "ready": True,
                "apiKeyConfigured": True,
            },
            "embedding": {
                "provider": "openai-compatible",
                "model": "text-embedding-test",
                "ready": True,
                "apiKeyConfigured": True,
            },
        }


def _set_ai_env(monkeypatch):
    monkeypatch.setenv("AGENTMEMORY_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("AGENTMEMORY_LLM_API_KEY", "test-llm-key")
    monkeypatch.setenv("AGENTMEMORY_LLM_MODEL", "gpt-test")
    monkeypatch.setenv("AGENTMEMORY_EMBEDDING_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("AGENTMEMORY_EMBEDDING_API_KEY", "test-embedding-key")
    monkeypatch.setenv("AGENTMEMORY_EMBEDDING_MODEL", "text-embedding-test")


def test_doctor_command_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "doctor.sqlite3"))
    _set_ai_env(monkeypatch)

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "AgentMemory doctor" in result.output
    assert "LLM provider: openai-compatible model=gpt-test ready=True" in result.output
    assert "Embedding provider: openai-compatible model=text-embedding-test ready=True" in result.output
    assert "test-llm-key" not in result.output
    assert "test-embedding-key" not in result.output
    assert "Status: ok" in result.output


def test_doctor_fails_when_ai_settings_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "doctor.sqlite3"))

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "AI providers: missing" in result.output
    assert "AGENTMEMORY_LLM_BASE_URL" in result.output


def test_memory_core_cli_commands(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "cli.sqlite3"))
    _set_ai_env(monkeypatch)
    monkeypatch.setattr(cli_module, "create_provider_bundle", lambda _settings: _StubProviderBundle())
    runner = CliRunner()

    observe = runner.invoke(
        app,
        [
            "observe",
            "--content",
            "Implemented CLI memory core commands.",
            "--session-id",
            "ses_cli",
            "--type",
            "work-summary",
            "--language",
            "en",
            "--project",
            "agentmemory",
            "--files",
            "src/agentmemory/cli.py,tests/test_cli.py",
            "--concepts",
            "cli,memory-core",
        ],
    )
    remember = runner.invoke(
        app,
        [
            "remember",
            "--content",
            "CLI list commands support JSON output.",
            "--type",
            "decision",
            "--language",
            "en",
            "--concepts",
            "cli,json",
            "--json",
        ],
    )
    sessions = runner.invoke(app, ["sessions", "--json"])
    memories = runner.invoke(app, ["memories", "--json"])
    audit = runner.invoke(app, ["audit", "--json"])
    summaries = runner.invoke(app, ["summaries", "--json"])
    candidates = runner.invoke(app, ["memory-candidates", "--json"])
    jobs = runner.invoke(app, ["llm-processing-jobs", "--json"])

    assert observe.exit_code == 0
    assert "Observation saved:" in observe.output
    assert remember.exit_code == 0
    assert json.loads(remember.output)["memory"]["type"] == "decision"
    assert sessions.exit_code == 0
    assert memories.exit_code == 0
    assert audit.exit_code == 0
    assert summaries.exit_code == 0
    assert candidates.exit_code == 0
    assert jobs.exit_code == 0

    session_items = json.loads(sessions.output)["sessions"]
    memory_items = json.loads(memories.output)["memories"]
    audit_items = json.loads(audit.output)["audit"]
    summary_items = json.loads(summaries.output)["summaries"]
    candidate_items = json.loads(candidates.output)["memoryCandidates"]
    job_items = json.loads(jobs.output)["llmProcessingJobs"]

    assert session_items[0]["id"] == "ses_cli"
    assert session_items[0]["observationCount"] == 1
    assert memory_items[0]["content"] == "CLI list commands support JSON output."
    assert [item["action"] for item in audit_items] == ["observe", "llm_processing_done", "remember"]
    assert summary_items[0]["content"] == "Stub summary"
    assert candidate_items[0]["status"] == "candidate"
    assert job_items[0]["status"] == "done"


def test_memory_core_cli_commands_require_ai_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "cli.sqlite3"))

    result = CliRunner().invoke(app, ["observe", "--content", "should fail"])

    assert result.exit_code != 0
    assert "Missing required AI provider settings" in str(result.exception)
