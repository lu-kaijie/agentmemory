from __future__ import annotations

from agentmemory.core.ids import generate_id, utc_now_iso
from agentmemory.core.models import (
    AuditRecord,
    ForgetRequest,
    ForgetResponse,
    GovernanceExport,
    IndexJobRecord,
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
from agentmemory.core.search import MemorySearchService, memory_document, observation_document, summary_document
from agentmemory.providers import LLMProvider
from agentmemory.state import StateKV
from agentmemory.state.schema import KV
from agentmemory.version import __version__


class MemoryNotFoundError(ValueError):
    def __init__(self, memory_id: str):
        super().__init__(f"Memory not found: {memory_id}")
        self.memory_id = memory_id


class MemoryCoreService:
    def __init__(
        self,
        kv: StateKV,
        llm: LLMProvider | None = None,
        search: MemorySearchService | None = None,
    ):
        self.kv = kv
        self.llm = llm
        self.search_service = search

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
        if self.search_service:
            self.search_service.index_document(observation_document(observation))
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
                if self.search_service:
                    self.search_service.index_document(summary_document(summary, observation))
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
        if self.search_service:
            self.search_service.index_document(memory_document(memory))
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

    def list_observations(self) -> list[ObservationRecord]:
        observations: list[ObservationRecord] = []
        for session in self.list_sessions():
            observations.extend(
                ObservationRecord.model_validate(item)
                for item in self.kv.list(KV.observations(session.id))
            )
        return sorted(observations, key=lambda item: item.createdAt)

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

    def list_index_jobs(self) -> list[IndexJobRecord]:
        items = [IndexJobRecord.model_validate(item) for item in self.kv.list(KV.index_jobs)]
        return sorted(items, key=lambda item: item.startedAt)

    def export_data(self, source: str = "cli") -> GovernanceExport:
        now = utc_now_iso()
        sessions = self.list_sessions()
        observations = self.list_observations()
        memories = self.list_memories()
        summaries = self.list_summaries()
        memory_candidates = self.list_memory_candidates()
        llm_processing_jobs = self.list_llm_processing_jobs()
        index_jobs = self.list_index_jobs()
        audit = AuditRecord(
            id=generate_id("aud"),
            action="export",
            targetType="governance",
            targetId="agentmemory",
            source=source,
            timestamp=now,
            details={
                "sessions": len(sessions),
                "observations": len(observations),
                "memories": len(memories),
                "summaries": len(summaries),
                "memoryCandidates": len(memory_candidates),
                "llmProcessingJobs": len(llm_processing_jobs),
                "indexJobs": len(index_jobs),
            },
        )
        self._record_audit(audit)
        return GovernanceExport(
            version=__version__,
            exportedAt=now,
            sessions=sessions,
            observations=observations,
            memories=memories,
            summaries=summaries,
            memoryCandidates=memory_candidates,
            llmProcessingJobs=llm_processing_jobs,
            indexJobs=index_jobs,
            audit=self.list_audit(),
        )

    def forget(self, request: ForgetRequest) -> ForgetResponse:
        raw = self.kv.get(KV.memories, request.memoryId)
        if raw is None:
            raise MemoryNotFoundError(request.memoryId)
        memory = MemoryRecord.model_validate(raw)
        if self.search_service:
            self.search_service.delete_document("memory", request.memoryId)
        self.kv.delete(KV.memories, request.memoryId)
        now = utc_now_iso()
        audit = AuditRecord(
            id=generate_id("aud"),
            action="forget",
            targetType="memory",
            targetId=request.memoryId,
            source=request.source,
            timestamp=now,
            details={
                "reason": request.reason,
                "type": memory.type,
                "concepts": memory.concepts,
                "files": memory.files,
                "language": memory.language,
            },
        )
        self._record_audit(audit)
        return ForgetResponse(memoryId=request.memoryId, auditId=audit.id, deletedMemory=memory)

    def search(self, request):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.search(request)

    def smart_search(self, request):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.smart_search(request)

    def index_status(self):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.status()

    def index_rebuild(self):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.rebuild()

    def index_repair(self):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.repair()

    def _record_audit(self, record: AuditRecord) -> None:
        self.kv.set(KV.audit, record.id, record.model_dump())
