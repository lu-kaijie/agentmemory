from __future__ import annotations

from fastapi import FastAPI

from agentmemory.config import Settings, get_settings
from agentmemory.core import MemoryCoreService
from agentmemory.core.models import ObserveRequest, RememberRequest, SearchRequest, SmartSearchRequest
from agentmemory.core.search import MemorySearchService
from agentmemory.providers import create_provider_bundle
from agentmemory.state import StateKV
from agentmemory.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(title="AgentMemory", version=__version__)
    app.state.settings = resolved
    app.state.kv = StateKV(resolved.db_path)
    app.state.providers = create_provider_bundle(resolved)
    app.state.search_service = MemorySearchService(
        app.state.kv,
        settings=resolved,
        embedding=app.state.providers.embedding,
        llm=app.state.providers.llm,
    )
    app.state.memory_core = MemoryCoreService(
        app.state.kv,
        llm=app.state.providers.llm,
        search=app.state.search_service,
    )

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
            "providers": app.state.providers.health_summary(),
            "index": app.state.memory_core.index_status().model_dump(),
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

    @app.get("/agentmemory/summaries")
    def summaries() -> dict[str, object]:
        items = app.state.memory_core.list_summaries()
        return {"summaries": [item.model_dump() for item in items]}

    @app.get("/agentmemory/memory-candidates")
    def memory_candidates() -> dict[str, object]:
        items = app.state.memory_core.list_memory_candidates()
        return {"memoryCandidates": [item.model_dump() for item in items]}

    @app.get("/agentmemory/llm-processing-jobs")
    def llm_processing_jobs() -> dict[str, object]:
        items = app.state.memory_core.list_llm_processing_jobs()
        return {"llmProcessingJobs": [item.model_dump() for item in items]}

    @app.post("/agentmemory/search")
    def search(payload: SearchRequest) -> dict[str, object]:
        return app.state.memory_core.search(payload).model_dump()

    @app.post("/agentmemory/smart-search")
    def smart_search(payload: SmartSearchRequest) -> dict[str, object]:
        return app.state.memory_core.smart_search(payload).model_dump()

    @app.get("/agentmemory/index/status")
    def index_status() -> dict[str, object]:
        return app.state.memory_core.index_status().model_dump()

    @app.post("/agentmemory/index/rebuild")
    def index_rebuild() -> dict[str, object]:
        return app.state.memory_core.index_rebuild()

    @app.post("/agentmemory/index/repair")
    def index_repair() -> dict[str, object]:
        return app.state.memory_core.index_repair()

    return app
