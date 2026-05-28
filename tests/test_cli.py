import json

from typer.testing import CliRunner

from agentmemory.cli import app


def test_doctor_command_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "doctor.sqlite3"))

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "AgentMemory doctor" in result.output
    assert "Status: ok" in result.output


def test_memory_core_cli_commands(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTMEMORY_DB_PATH", str(tmp_path / "cli.sqlite3"))
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

    assert observe.exit_code == 0
    assert "Observation saved:" in observe.output
    assert remember.exit_code == 0
    assert json.loads(remember.output)["memory"]["type"] == "decision"
    assert sessions.exit_code == 0
    assert memories.exit_code == 0
    assert audit.exit_code == 0

    session_items = json.loads(sessions.output)["sessions"]
    memory_items = json.loads(memories.output)["memories"]
    audit_items = json.loads(audit.output)["audit"]

    assert session_items[0]["id"] == "ses_cli"
    assert session_items[0]["observationCount"] == 1
    assert memory_items[0]["content"] == "CLI list commands support JSON output."
    assert [item["action"] for item in audit_items] == ["observe", "remember"]
