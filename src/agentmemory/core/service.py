from __future__ import annotations

from agentmemory.core.ids import generate_id, utc_now_iso
from agentmemory.core.models import (
    AuditRecord,
    LLMProcessingJobRecord,
    MemoryCandidateRecord,
    MemoryRecord,
    ObserveRequest,
    ObserveResponse,
    ObservationRecord,
    RememberRequest,
    RememberResponse,
    SessionRecord,
    SummaryRecord,
)
from agentmemory.core.processing import create_running_job, process_observation
from agentmemory.providers import LLMProvider
from agentmemory.state import StateKV
from agentmemory.state.schema import KV


class MemoryCoreService:
    def __init__(self, kv: StateKV, llm: LLMProvider | None = None):
        self.kv = kv
        self.llm = llm

    def observe(self, request: ObserveRequest) -> ObserveResponse:
        now = utc_now_iso()
        session_id = request.sessionId or generate_id("ses")
        existing = self.kv.get(KV.sessions, session_id)
        if existing:
            session = SessionRecord.model_validate(existing)
            session.project = request.project or session.project
            session.cwd = request.cwd or session.cwd
            session.updatedAt = now
            session.observationCount += 1
        else:
            session = SessionRecord(
                id=session_id,
                project=request.project,
                cwd=request.cwd,
                startedAt=now,
                updatedAt=now,
                observationCount=1,
            )

        observation = ObservationRecord(
            id=generate_id("obs"),
            sessionId=session_id,
            type=request.type,
            content=request.content,
            source=request.source,
            language=request.language,
            project=request.project,
            cwd=request.cwd,
            files=request.files,
            concepts=request.concepts,
            createdAt=now,
        )

        self.kv.set(KV.sessions, session.id, session.model_dump())
        self.kv.set(KV.observations(session.id), observation.id, observation.model_dump())
        self._record_audit(
            AuditRecord(
                id=generate_id("aud"),
                action="observe",
                targetType="observation",
                targetId=observation.id,
                source=request.source,
                timestamp=now,
                details={"sessionId": session.id, "type": observation.type},
            ),
        )
        processing_job = None
        summary = None
        memory_candidates: list[MemoryCandidateRecord] = []
        if self.llm:
            processing_job = create_running_job(observation, now)
            self.kv.set(KV.llm_processing_jobs, processing_job.id, processing_job.model_dump())
            processing_job, summary, memory_candidates = process_observation(
                observation=observation,
                llm=self.llm,
                job=processing_job,
            )
            if summary:
                self.kv.set(KV.summaries, summary.id, summary.model_dump())
            for candidate in memory_candidates:
                self.kv.set(KV.memory_candidates, candidate.id, candidate.model_dump())
            self.kv.set(KV.llm_processing_jobs, processing_job.id, processing_job.model_dump())
            self._record_audit(
                AuditRecord(
                    id=generate_id("aud"),
                    action="llm_processing_done" if processing_job.status == "done" else "llm_processing_failed",
                    targetType="llm_processing_job",
                    targetId=processing_job.id,
                    source=request.source,
                    timestamp=processing_job.finishedAt or now,
                    details={
                        "observationId": observation.id,
                        "summaryId": processing_job.summaryId,
                        "candidateIds": processing_job.candidateIds,
                        "lastError": processing_job.lastError,
                    },
                ),
            )

        return ObserveResponse(
            observationId=observation.id,
            sessionId=session.id,
            observation=observation,
            processingJob=processing_job,
            summary=summary,
            memoryCandidates=memory_candidates,
        )

    def remember(self, request: RememberRequest) -> RememberResponse:
        now = utc_now_iso()
        memory = MemoryRecord(
            id=generate_id("mem"),
            type=request.type,
            content=request.content,
            concepts=request.concepts,
            files=request.files,
            language=request.language,
            source=request.source,
            canonicalId=request.canonicalId,
            duplicateOf=request.duplicateOf,
            relations=request.relations,
            createdAt=now,
        )
        self.kv.set(KV.memories, memory.id, memory.model_dump())
        self._record_audit(
            AuditRecord(
                id=generate_id("aud"),
                action="remember",
                targetType="memory",
                targetId=memory.id,
                source=request.source,
                timestamp=now,
                details={"type": memory.type},
            ),
        )
        return RememberResponse(memoryId=memory.id, memory=memory)

    def list_sessions(self) -> list[SessionRecord]:
        items = [SessionRecord.model_validate(item) for item in self.kv.list(KV.sessions)]
        return sorted(items, key=lambda item: item.updatedAt)

    def list_memories(self) -> list[MemoryRecord]:
        items = [MemoryRecord.model_validate(item) for item in self.kv.list(KV.memories)]
        return sorted(items, key=lambda item: item.createdAt)

    def list_audit(self) -> list[AuditRecord]:
        items = [AuditRecord.model_validate(item) for item in self.kv.list(KV.audit)]
        return sorted(items, key=lambda item: item.timestamp)

    def list_summaries(self) -> list[SummaryRecord]:
        items = [SummaryRecord.model_validate(item) for item in self.kv.list(KV.summaries)]
        return sorted(items, key=lambda item: item.createdAt)

    def list_memory_candidates(self) -> list[MemoryCandidateRecord]:
        items = [MemoryCandidateRecord.model_validate(item) for item in self.kv.list(KV.memory_candidates)]
        return sorted(items, key=lambda item: item.createdAt)

    def list_llm_processing_jobs(self) -> list[LLMProcessingJobRecord]:
        items = [LLMProcessingJobRecord.model_validate(item) for item in self.kv.list(KV.llm_processing_jobs)]
        return sorted(items, key=lambda item: item.startedAt)

    def _record_audit(self, record: AuditRecord) -> None:
        self.kv.set(KV.audit, record.id, record.model_dump())
