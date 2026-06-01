from __future__ import annotations

from importlib import resources

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from agentmemory.config import Settings, get_settings
from agentmemory.core import MemoryCoreService
from agentmemory.core.models import (
    ContextRequest,
    ForgetRequest,
    GovernanceImportRequest,
    CrystalCreateRequest,
    LessonRecallRequest,
    MaintenanceRunRequest,
    ObserveRequest,
    PinMemoryRequest,
    ProjectProfileUpdateRequest,
    RememberRequest,
    SearchRequest,
    SmartSearchRequest,
    WikiConsolidateRequest,
    WikiFileAnswerRequest,
    WikiReflectRequest,
)
from agentmemory.core.search import MemorySearchService
from agentmemory.core.service import MemoryNotFoundError
from agentmemory.providers import create_provider_bundle
from agentmemory.state import StateKV
from agentmemory.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()

    def respond(payload: dict[str, object], envelope: bool = False) -> dict[str, object]:
        if envelope or resolved.rest_envelope:
            return {"status_code": 200, "body": payload, "headers": {}}
        return payload

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

    viewer_root = resources.files("agentmemory.viewer")
    viewer_dist = viewer_root.joinpath("dist")
    viewer_index = viewer_dist.joinpath("index.html")
    if viewer_dist.joinpath("assets").is_dir():
        app.mount(
            "/agentmemory/assets",
            StaticFiles(directory=str(viewer_dist.joinpath("assets"))),
            name="agentmemory-viewer-assets",
        )

    @app.get("/agentmemory/", response_class=HTMLResponse)
    def viewer() -> Response:
        if viewer_index.is_file():
            return FileResponse(str(viewer_index), media_type="text/html")
        html = viewer_root.joinpath("index.html").read_text(encoding="utf-8")
        return HTMLResponse(html)

    @app.get("/agentmemory/livez")
    def livez() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/agentmemory/health")
    def health(envelope: bool = False) -> dict[str, object]:
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
        return respond(body, envelope)

    @app.post("/agentmemory/observe")
    def observe(payload: ObserveRequest) -> dict[str, object]:
        result = app.state.memory_core.observe(payload)
        return result.model_dump()

    @app.post("/agentmemory/remember")
    def remember(payload: RememberRequest) -> dict[str, object]:
        result = app.state.memory_core.remember(payload)
        return result.model_dump()

    @app.get("/agentmemory/projects")
    def projects() -> dict[str, object]:
        items = app.state.memory_core.list_projects()
        return {"projects": [item.model_dump() for item in items]}

    @app.post("/agentmemory/project/profile/update")
    def project_profile_update(payload: ProjectProfileUpdateRequest) -> dict[str, object]:
        return app.state.memory_core.update_project_profile(payload).model_dump()

    @app.get("/agentmemory/project/profile/{project_id}")
    def project_profile(project_id: str) -> dict[str, object]:
        project = app.state.memory_core.get_project(project_id)
        profile = app.state.memory_core.project_profile(project_id)
        return {
            "project": project.model_dump() if project else None,
            "profile": profile.model_dump() if profile else None,
        }

    @app.post("/agentmemory/pins")
    def pin_memory(payload: PinMemoryRequest) -> dict[str, object]:
        return app.state.memory_core.pin_memory(payload).model_dump()

    @app.get("/agentmemory/pins")
    def pins() -> dict[str, object]:
        items = app.state.memory_core.list_pinned_memory()
        return {"pinnedMemory": [item.model_dump() for item in items]}

    @app.post("/agentmemory/pins/{pin_id}/disable")
    def pin_disable(pin_id: str) -> dict[str, object]:
        return {"pinned": app.state.memory_core.disable_pinned_memory(pin_id).model_dump()}

    @app.delete("/agentmemory/pins/{pin_id}")
    def pin_delete(pin_id: str) -> dict[str, object]:
        return {"deleted": app.state.memory_core.delete_pinned_memory(pin_id), "pinId": pin_id}

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

    @app.post("/agentmemory/import")
    def import_data(payload: dict[str, object]) -> dict[str, object]:
        try:
            return app.state.memory_core.import_data(GovernanceImportRequest(payload=payload, source="rest")).model_dump()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"error": "invalid_import", "message": str(exc)}) from exc

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

    @app.get("/agentmemory/wiki/insights")
    def wiki_insights() -> dict[str, object]:
        items = app.state.memory_core.list_insights()
        return {"insights": [item.model_dump() for item in items]}

    @app.post("/agentmemory/wiki/consolidate")
    def wiki_consolidate(payload: WikiConsolidateRequest | None = None) -> dict[str, object]:
        return app.state.memory_core.consolidate_wiki(payload or WikiConsolidateRequest()).model_dump()

    @app.post("/agentmemory/wiki/lesson-recall")
    def wiki_lesson_recall(payload: LessonRecallRequest) -> dict[str, object]:
        return app.state.memory_core.recall_lessons(payload).model_dump()

    @app.post("/agentmemory/wiki/crystallize")
    def wiki_crystallize(payload: CrystalCreateRequest) -> dict[str, object]:
        return app.state.memory_core.create_crystal(payload).model_dump()

    @app.post("/agentmemory/wiki/reflect")
    def wiki_reflect(payload: WikiReflectRequest | None = None) -> dict[str, object]:
        return app.state.memory_core.reflect_wiki(payload or WikiReflectRequest()).model_dump()

    @app.post("/agentmemory/wiki/lint")
    def wiki_lint() -> dict[str, object]:
        return app.state.memory_core.lint_wiki().model_dump()

    @app.post("/agentmemory/wiki/file-answer")
    def wiki_file_answer(payload: WikiFileAnswerRequest) -> dict[str, object]:
        return app.state.memory_core.file_wiki_answer(payload).model_dump()

    @app.post("/agentmemory/maintenance/run")
    def maintenance_run(payload: MaintenanceRunRequest | None = None, envelope: bool = False) -> dict[str, object]:
        result = app.state.memory_core.run_maintenance(payload or MaintenanceRunRequest()).model_dump()
        return respond(result, envelope)

    @app.post("/agentmemory/search")
    def search(payload: SearchRequest) -> dict[str, object]:
        return app.state.memory_core.search(payload).model_dump()

    @app.post("/agentmemory/smart-search")
    def smart_search(payload: SmartSearchRequest) -> dict[str, object]:
        return app.state.memory_core.smart_search(payload).model_dump()

    @app.post("/agentmemory/context")
    def context(payload: ContextRequest) -> dict[str, object]:
        return app.state.memory_core.context(payload).model_dump()

    @app.get("/agentmemory/index/status")
    def index_status() -> dict[str, object]:
        return app.state.memory_core.index_status().model_dump()

    return app
