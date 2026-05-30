import json

from typer.testing import CliRunner

import agentmemory.cli as cli_module
from agentmemory.cli import app
from conftest import StubEmbeddingProvider, StubLLMProvider


class _StubProviderBundle:
    llm = StubLLMProvider()
    embedding = StubEmbeddingProvider()

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
    monkeypatch.setenv("AGENTMEMORY_VECTOR_DB_PATH", str(tmp_path / "vector"))
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
    monkeypatch.setenv("AGENTMEMORY_VECTOR_DB_PATH", str(tmp_path / "vector"))

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "AI providers: missing" in result.output
    assert "AGENTMEMORY_LLM_BASE_URL" in result.output


def test_memory_core_cli_commands(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "cli.sqlite3"))
    monkeypatch.setenv("AGENTMEMORY_VECTOR_DB_PATH", str(tmp_path / "vector"))
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
    search = runner.invoke(app, ["search", "CLI", "--json"])
    smart = runner.invoke(app, ["smart-search", "CLI memory", "--json"])
    index_status = runner.invoke(app, ["index", "status", "--json"])
    index_repair = runner.invoke(app, ["index", "repair", "--json"])
    index_rebuild = runner.invoke(app, ["index", "rebuild", "--json"])
    exported = runner.invoke(app, ["export", "--json"])
    wiki_jobs = runner.invoke(app, ["wiki", "jobs", "--json"])
    wiki_update = runner.invoke(app, ["wiki", "update", "--limit", "1", "--json"])
    wiki_knowledge = runner.invoke(app, ["wiki", "knowledge", "--json"])
    wiki_pages = runner.invoke(app, ["wiki", "pages", "--json"])

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
    assert search.exit_code == 0
    assert smart.exit_code == 0
    assert index_status.exit_code == 0
    assert index_repair.exit_code == 0
    assert index_rebuild.exit_code == 0
    assert exported.exit_code == 0
    assert wiki_jobs.exit_code == 0
    assert wiki_update.exit_code == 0
    assert wiki_knowledge.exit_code == 0
    assert wiki_pages.exit_code == 0

    session_items = json.loads(sessions.output)["sessions"]
    memory_items = json.loads(memories.output)["memories"]
    audit_items = json.loads(audit.output)["audit"]
    summary_items = json.loads(summaries.output)["summaries"]
    candidate_items = json.loads(candidates.output)["memoryCandidates"]
    job_items = json.loads(jobs.output)["llmProcessingJobs"]
    search_items = json.loads(search.output)["results"]
    smart_payload = json.loads(smart.output)
    index_payload = json.loads(index_status.output)
    export_payload = json.loads(exported.output)
    wiki_jobs_payload = json.loads(wiki_jobs.output)
    wiki_update_payload = json.loads(wiki_update.output)
    wiki_knowledge_payload = json.loads(wiki_knowledge.output)
    wiki_pages_payload = json.loads(wiki_pages.output)

    assert session_items[0]["id"] == "ses_cli"
    assert session_items[0]["observationCount"] == 1
    assert memory_items[0]["content"] == "CLI list commands support JSON output."
    assert [item["action"] for item in audit_items] == ["observe", "llm_processing_done", "remember"]
    assert summary_items[0]["content"] == "Stub summary"
    assert candidate_items[0]["status"] == "candidate"
    assert job_items[0]["status"] == "done"
    assert search_items
    assert smart_payload["answer"] == "stub explanation"
    assert smart_payload["evidence"]
    assert index_payload["documents"] >= 2
    assert export_payload["memories"][0]["content"] == "CLI list commands support JSON output."
    assert export_payload["audit"][-1]["action"] == "export"
    assert wiki_jobs_payload["wikiUpdateJobs"]
    assert wiki_update_payload["jobs"][0]["status"] == "applied"
    assert {item["kind"] for item in wiki_knowledge_payload["knowledge"]} == {"semantic", "procedural", "lesson", "crystal"}
    assert wiki_pages_payload["wikiPages"][0]["content"] == "Stub wiki update"


def test_memory_governance_cli_commands(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "governance-cli.sqlite3"))
    monkeypatch.setenv("AGENTMEMORY_VECTOR_DB_PATH", str(tmp_path / "vector"))
    _set_ai_env(monkeypatch)
    monkeypatch.setattr(cli_module, "create_provider_bundle", lambda _settings: _StubProviderBundle())
    runner = CliRunner()

    remember = runner.invoke(
        app,
        [
            "remember",
            "--content",
            "CLI forget removes this memory.",
            "--language",
            "en",
            "--json",
        ],
    )
    memory_id = json.loads(remember.output)["memoryId"]
    before = runner.invoke(app, ["search", "CLI forget", "--mode", "keyword", "--json"])
    forget = runner.invoke(app, ["forget", "--memory-id", memory_id, "--reason", "cli test", "--json"])
    after_memories = runner.invoke(app, ["memories", "--json"])
    after_search = runner.invoke(app, ["search", "CLI forget", "--mode", "hybrid", "--json"])
    audit = runner.invoke(app, ["audit", "--json"])
    missing = runner.invoke(app, ["forget", "--memory-id", memory_id, "--json"])

    assert remember.exit_code == 0
    assert json.loads(before.output)["results"]
    assert forget.exit_code == 0
    forget_payload = json.loads(forget.output)
    assert forget_payload["memoryId"] == memory_id
    assert forget_payload["auditId"].startswith("aud_")
    assert after_memories.exit_code == 0
    assert json.loads(after_memories.output)["memories"] == []
    assert after_search.exit_code == 0
    assert json.loads(after_search.output)["results"] == []
    assert [item["action"] for item in json.loads(audit.output)["audit"]] == ["remember", "forget"]
    assert missing.exit_code == 1
    assert json.loads(missing.output)["error"] == "memory_not_found"


def test_wiki_cli_rebuild(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "wiki-cli.sqlite3"))
    monkeypatch.setenv("AGENTMEMORY_VECTOR_DB_PATH", str(tmp_path / "vector"))
    _set_ai_env(monkeypatch)
    monkeypatch.setattr(cli_module, "create_provider_bundle", lambda _settings: _StubProviderBundle())
    runner = CliRunner()

    remember = runner.invoke(app, ["remember", "--content", "CLI Wiki rebuild evidence.", "--language", "en"])
    rebuild = runner.invoke(app, ["wiki", "rebuild", "--all", "--json"])
    pages = runner.invoke(app, ["wiki", "pages", "--json"])
    knowledge = runner.invoke(app, ["wiki", "knowledge", "--json"])
    jobs = runner.invoke(app, ["wiki", "jobs", "--json"])

    assert remember.exit_code == 0
    assert rebuild.exit_code == 0
    assert len(json.loads(rebuild.output)["pages"]) == 6
    assert pages.exit_code == 0
    assert len(json.loads(pages.output)["wikiPages"]) == 6
    assert knowledge.exit_code == 0
    assert len(json.loads(knowledge.output)["knowledge"]) == 24
    assert jobs.exit_code == 0
    assert json.loads(jobs.output)["wikiUpdateJobs"]


def test_memory_core_cli_commands_require_ai_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "cli.sqlite3"))
    monkeypatch.setenv("AGENTMEMORY_VECTOR_DB_PATH", str(tmp_path / "vector"))

    result = CliRunner().invoke(app, ["observe", "--content", "should fail"])

    assert result.exit_code != 0
    assert "Missing required AI provider settings" in str(result.exception)
