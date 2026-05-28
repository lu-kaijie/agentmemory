from __future__ import annotations

from fastapi import FastAPI

from agentmemory.config import Settings, get_settings
from agentmemory.core import MemoryCoreService
from agentmemory.core.models import ObserveRequest, RememberRequest
from agentmemory.state import StateKV
from agentmemory.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(title="AgentMemory", version=__version__)
    app.state.settings = resolved
    app.state.kv = StateKV(resolved.db_path)
    app.state.memory_core = MemoryCoreService(app.state.kv)

    @app.get("/agentmemory/livez")
    def livez() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/agentmemory/health")
    def health() -> dict[str, object]:
        database_ok = False
        error = None
        try:
            database_ok = bool(app.state.kv.probe())
        except Exception as exc:  # pragma: no cover - defensive surface
            error = str(exc)
        status = "ok" if database_ok else "error"
        body: dict[str, object] = {
            "service": "agentmemory",
            "version": __version__,
            "status": status,
            "database": {"ok": database_ok},
            "config": resolved.safe_summary(),
        }
        if error:
            body["database"]["error"] = error  # type: ignore[index]
        return body

    @app.post("/agentmemory/observe")
    def observe(payload: ObserveRequest) -> dict[str, object]:
        result = app.state.memory_core.observe(payload)
        return result.model_dump()

    @app.post("/agentmemory/remember")
    def remember(payload: RememberRequest) -> dict[str, object]:
        result = app.state.memory_core.remember(payload)
        return result.model_dump()

    @app.get("/agentmemory/sessions")
    def sessions() -> dict[str, object]:
        items = app.state.memory_core.list_sessions()
        return {"sessions": [item.model_dump() for item in items]}

    @app.get("/agentmemory/memories")
    def memories() -> dict[str, object]:
        items = app.state.memory_core.list_memories()
        return {"memories": [item.model_dump() for item in items]}

    @app.get("/agentmemory/audit")
    def audit() -> dict[str, object]:
        items = app.state.memory_core.list_audit()
        return {"audit": [item.model_dump() for item in items]}

    return app
