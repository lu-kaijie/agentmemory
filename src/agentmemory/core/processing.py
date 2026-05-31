from __future__ import annotations

from typing import Any

from agentmemory.providers import LLMProvider

from .ids import generate_id, utc_now_iso
from .models import (
    LLMProcessingJobRecord,
    MemoryCandidateRecord,
    ObservationRecord,
    SummaryRecord,
)


def create_pending_job(observation: ObservationRecord, now: str | None = None) -> LLMProcessingJobRecord:
    return LLMProcessingJobRecord(
        id=generate_id("job"),
        observationId=observation.id,
        status="pending",
        startedAt=now or utc_now_iso(),
    )


def create_running_job(observation: ObservationRecord, now: str | None = None) -> LLMProcessingJobRecord:
    return LLMProcessingJobRecord(
        id=generate_id("job"),
        observationId=observation.id,
        status="running",
        startedAt=now or utc_now_iso(),
    )


def process_observation(
    observation: ObservationRecord,
    llm: LLMProvider,
    job: LLMProcessingJobRecord,
) -> tuple[LLMProcessingJobRecord, SummaryRecord | None, list[MemoryCandidateRecord]]:
    try:
        summary_content = llm.summarize(
            observation.content,
            "Summarize this coding-agent observation into one concise memory summary.",
        )
        candidate_items = llm.extract_memories(observation.content)
        finished_at = utc_now_iso()
        summary = SummaryRecord(
            id=generate_id("sum"),
            observationId=observation.id,
            kind="observation",
            content=summary_content,
            language=observation.language,
            scope="project",
            project=observation.project,
            projectId=observation.projectId,
            createdAt=finished_at,
        )
        candidates = [
            _candidate_from_llm_item(observation, item, finished_at)
            for item in candidate_items
            if _candidate_content(item)
        ]
        job.status = "done"
        job.summaryId = summary.id
        job.candidateIds = [candidate.id for candidate in candidates]
        job.lastError = None
        job.finishedAt = finished_at
        return job, summary, candidates
    except Exception as exc:
        finished_at = utc_now_iso()
        job.status = "failed"
        job.lastError = str(exc)
        job.finishedAt = finished_at
        return job, None, []


def _candidate_from_llm_item(
    observation: ObservationRecord,
    item: dict[str, Any],
    created_at: str,
) -> MemoryCandidateRecord:
    return MemoryCandidateRecord(
        id=generate_id("cand"),
        observationId=observation.id,
        content=_candidate_content(item),
        type=str(item.get("type") or "fact"),
        confidence=_coerce_confidence(item.get("confidence")),
        concepts=_string_list(item.get("concepts")) or observation.concepts,
        files=_string_list(item.get("files")) or observation.files,
        language=observation.language,
        createdAt=created_at,
    )


def _candidate_content(item: dict[str, Any]) -> str:
    value = item.get("content") or item.get("memory") or item.get("text")
    return str(value).strip() if value else ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _coerce_confidence(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, numeric))
