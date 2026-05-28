from __future__ import annotations

import json

import typer
import uvicorn

from agentmemory.api.app import create_app
from agentmemory.config import get_settings
from agentmemory.core.models import ObserveRequest, RememberRequest
from agentmemory.core.service import MemoryCoreService
from agentmemory.providers import MissingAIProviderSettings, create_provider_bundle, require_ai_settings
from agentmemory.state import StateKV

app = typer.Typer(help="AgentMemory local service")


@app.command()
def serve() -> None:
    """Start the AgentMemory API service."""
    settings = get_settings()
    uvicorn.run(
        "agentmemory.api.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


@app.command()
def doctor() -> None:
    """Run local configuration and database checks."""
    settings = get_settings()
    typer.echo("AgentMemory doctor")
    typer.echo(f"Host: {settings.host}")
    typer.echo(f"Port: {settings.port}")
    typer.echo(f"Database: {settings.db_path}")
    typer.echo(f"Secret configured: {'yes' if settings.secret else 'no'}")
    try:
        providers = create_provider_bundle(settings)
    except MissingAIProviderSettings as exc:
        typer.echo(f"AI providers: missing ({', '.join(exc.missing_settings)})")
        raise typer.Exit(code=1) from exc

    provider_status = providers.health_summary()
    llm = provider_status["llm"]
    embedding = provider_status["embedding"]
    typer.echo(f"LLM provider: {llm['provider']} model={llm['model']} ready={llm['ready']}")
    typer.echo(
        "LLM API key configured: "
        f"{'yes' if llm['apiKeyConfigured'] else 'no'}",
    )
    typer.echo(
        f"Embedding provider: {embedding['provider']} "
        f"model={embedding['model']} ready={embedding['ready']}",
    )
    typer.echo(
        "Embedding API key configured: "
        f"{'yes' if embedding['apiKeyConfigured'] else 'no'}",
    )

    kv = StateKV(settings.db_path)
    kv.probe()
    create_app(settings)
    typer.echo("Status: ok")


def _memory_core() -> MemoryCoreService:
    settings = get_settings()
    require_ai_settings(settings)
    return MemoryCoreService(StateKV(settings.db_path))


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _emit(value: object, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        typer.echo(value)


@app.command()
def observe(
    content: str = typer.Option(..., "--content", "-c", help="Observation content."),
    session_id: str | None = typer.Option(None, "--session-id", help="Session id."),
    type: str = typer.Option("work-summary", "--type", help="Observation type."),
    language: str = typer.Option("unknown", "--language", help="zh, en, mixed, or unknown."),
    project: str | None = typer.Option(None, "--project", help="Project name or path."),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory."),
    files: str | None = typer.Option(None, "--files", help="Comma-separated file paths."),
    concepts: str | None = typer.Option(None, "--concepts", help="Comma-separated concepts."),
    json_output: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    """Save a work observation."""
    result = _memory_core().observe(
        ObserveRequest(
            content=content,
            sessionId=session_id,
            type=type,
            language=language,  # type: ignore[arg-type]
            project=project,
            cwd=cwd,
            files=_split_csv(files),
            concepts=_split_csv(concepts),
        ),
    )
    if json_output:
        _emit(result.model_dump(), True)
    else:
        typer.echo(f"Observation saved: {result.observationId} (session {result.sessionId})")


@app.command()
def remember(
    content: str = typer.Option(..., "--content", "-c", help="Memory content."),
    type: str = typer.Option("fact", "--type", help="Memory type."),
    language: str = typer.Option("unknown", "--language", help="zh, en, mixed, or unknown."),
    concepts: str | None = typer.Option(None, "--concepts", help="Comma-separated concepts."),
    files: str | None = typer.Option(None, "--files", help="Comma-separated file paths."),
    json_output: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    """Save an explicit long-term memory."""
    result = _memory_core().remember(
        RememberRequest(
            content=content,
            type=type,
            language=language,  # type: ignore[arg-type]
            concepts=_split_csv(concepts),
            files=_split_csv(files),
        ),
    )
    if json_output:
        _emit(result.model_dump(), True)
    else:
        typer.echo(f"Memory saved: {result.memoryId}")


@app.command("sessions")
def list_sessions(json_output: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    """List sessions."""
    items = [item.model_dump() for item in _memory_core().list_sessions()]
    if json_output:
        _emit({"sessions": items}, True)
    else:
        for item in items:
            typer.echo(f"{item['id']} observations={item['observationCount']} updated={item['updatedAt']}")


@app.command("memories")
def list_memories(json_output: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    """List memories."""
    items = [item.model_dump() for item in _memory_core().list_memories()]
    if json_output:
        _emit({"memories": items}, True)
    else:
        for item in items:
            typer.echo(f"{item['id']} [{item['type']}] {item['content']}")


@app.command("audit")
def list_audit(json_output: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    """List audit records."""
    items = [item.model_dump() for item in _memory_core().list_audit()]
    if json_output:
        _emit({"audit": items}, True)
    else:
        for item in items:
            typer.echo(f"{item['id']} {item['action']} {item['targetType']}:{item['targetId']}")
