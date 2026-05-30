from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from importlib import resources

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from agentmemory.config import Settings, get_settings
from agentmemory.core import MemoryCoreService
from agentmemory.core.models import (
    ForgetRequest,
    ObserveRequest,
    RememberRequest,
    SearchRequest,
    SmartSearchRequest,
    WikiRebuildRequest,
    WikiUpdateRequest,
)
from agentmemory.core.search import MemorySearchService
from agentmemory.core.service import MemoryNotFoundError
from agentmemory.providers import create_provider_bundle
from agentmemory.state import StateKV
from agentmemory.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stop_index_worker = asyncio.Event()
        stop_wiki_worker = asyncio.Event()
        index_worker = asyncio.create_task(app.state.search_service.run_pending_worker(stop_index_worker))
        wiki_worker = asyncio.create_task(app.state.memory_core.run_wiki_worker(stop_wiki_worker))
        try:
            yield
        finally:
            stop_index_worker.set()
            stop_wiki_worker.set()
            await index_worker
            await wiki_worker

    app = FastAPI(title="AgentMemory", version=__version__, lifespan=lifespan)
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

    @app.get("/agentmemory/", response_class=HTMLResponse)
    def viewer() -> HTMLResponse:
        html = resources.files("agentmemory.viewer").joinpath("index.html").read_text(encoding="utf-8")
        return HTMLResponse(html)

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

    @app.get("/agentmemory/export")
    def export_data() -> dict[str, object]:
        return app.state.memory_core.export_data(source="rest").model_dump()

    @app.post("/agentmemory/forget")
    def forget(payload: ForgetRequest) -> dict[str, object]:
        try:
            return app.state.memory_core.forget(payload).model_dump()
        except MemoryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"error": "memory_not_found", "memoryId": exc.memory_id}) from exc

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

    @app.get("/agentmemory/wiki/pages")
    def wiki_pages() -> dict[str, object]:
        items = app.state.memory_core.list_wiki_pages()
        return {"wikiPages": [item.model_dump() for item in items]}

    @app.get("/agentmemory/wiki/jobs")
    def wiki_jobs() -> dict[str, object]:
        items = app.state.memory_core.list_wiki_jobs()
        return {"wikiUpdateJobs": [item.model_dump() for item in items]}

    @app.get("/agentmemory/wiki/knowledge")
    def wiki_knowledge() -> dict[str, object]:
        items = app.state.memory_core.list_knowledge()
        return {"knowledge": [item.model_dump() for item in items]}

    @app.post("/agentmemory/wiki/update")
    def wiki_update(payload: WikiUpdateRequest | None = None) -> dict[str, object]:
        return app.state.memory_core.process_wiki_updates(payload or WikiUpdateRequest()).model_dump()

    @app.post("/agentmemory/wiki/rebuild")
    def wiki_rebuild(payload: WikiRebuildRequest) -> dict[str, object]:
        return app.state.memory_core.rebuild_wiki(payload).model_dump()

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
