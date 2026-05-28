from agentmemory.core.models import ObserveRequest, RememberRequest
from agentmemory.core.service import MemoryCoreService
from agentmemory.state import StateKV


def test_observe_creates_and_updates_session(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))

    first = service.observe(
        ObserveRequest(
            sessionId="ses_test",
            content="Read PROJECT.md and confirmed the bootstrap scope.",
            project="agentmemory",
            cwd="/repo",
            files=["PROJECT.md"],
            concepts=["bootstrap"],
            language="en",
        ),
    )
    second = service.observe(
        ObserveRequest(
            sessionId="ses_test",
            content="Added memory core design notes.",
            project="agentmemory",
            cwd="/repo",
            language="en",
        ),
    )

    sessions = service.list_sessions()
    audit = service.list_audit()

    assert first.sessionId == "ses_test"
    assert second.sessionId == "ses_test"
    assert len(sessions) == 1
    assert sessions[0].observationCount == 2
    assert sessions[0].updatedAt >= sessions[0].startedAt
    assert [record.action for record in audit] == ["observe", "observe"]


def test_remember_saves_memory_and_audit(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))

    result = service.remember(
        RememberRequest(
            content="Use Python/FastAPI for the backend service foundation.",
            type="decision",
            concepts=["fastapi", "backend"],
            files=["PROJECT.md"],
            language="en",
        ),
    )

    memories = service.list_memories()
    audit = service.list_audit()

    assert result.memoryId.startswith("mem_")
    assert len(memories) == 1
    assert memories[0].content == "Use Python/FastAPI for the backend service foundation."
    assert memories[0].concepts == ["fastapi", "backend"]
    assert audit[-1].action == "remember"
    assert audit[-1].targetId == result.memoryId


def test_multilingual_duplicate_candidate_is_not_merged(tmp_path):
    service = MemoryCoreService(StateKV(tmp_path / "memory.sqlite3"))

    service.remember(
        RememberRequest(
            content="后端选择 FastAPI，因为 Python 的 RAG 生态更成熟。",
            type="decision",
            language="zh",
        ),
    )
    service.remember(
        RememberRequest(
            content="Backend uses FastAPI because Python has a stronger RAG ecosystem.",
            type="decision",
            language="en",
        ),
    )

    memories = service.list_memories()

    assert len(memories) == 2
    assert {memory.language for memory in memories} == {"zh", "en"}
    assert all(memory.duplicateOf is None for memory in memories)
