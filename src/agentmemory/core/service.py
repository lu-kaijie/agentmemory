from __future__ import annotations

import hashlib
import re
import asyncio

from agentmemory.core.ids import generate_id, utc_now_iso
from agentmemory.core.models import (
    AuditRecord,
    ContextRequest,
    ForgetRequest,
    ForgetResponse,
    GovernanceExport,
    GovernanceImportRequest,
    GovernanceImportResponse,
    IndexJobRecord,
    InsightRecord,
    KnowledgeRecord,
    LessonRecallRequest,
    LessonRecallResponse,
    LLMProcessingJobRecord,
    MaintenanceRunRequest,
    MaintenanceRunResponse,
    MemoryCandidateRecord,
    MemoryRecord,
    MemoryScope,
    ObserveRequest,
    ObserveResponse,
    ObservationRecord,
    PinnedMemoryRecord,
    PinMemoryRequest,
    PinMemoryResponse,
    ProjectProfileRecord,
    ProjectProfileUpdateRequest,
    ProjectProfileUpdateResponse,
    ProjectRecord,
    RememberRequest,
    RememberResponse,
    SummaryRecord,
    WIKI_TOPICS,
    CrystalCreateRequest,
    CrystalCreateResponse,
    WikiConsolidateRequest,
    WikiConsolidateResponse,
    WikiFileAnswerRequest,
    WikiFileAnswerResponse,
    WikiLintIssue,
    WikiLintResponse,
    WikiPageRecord,
    WikiReflectRequest,
    WikiReflectResponse,
    WikiRebuildRequest,
    WikiTopic,
    WikiUpdateJobRecord,
    WikiUpdateRequest,
    WikiUpdateResponse,
)
from agentmemory.core.processing import create_pending_job, process_observation
from agentmemory.core.scope import resolve_project_identity
from agentmemory.core.search import MemorySearchService, insight_document, knowledge_document, memory_document, observation_document, summary_document, wiki_page_document
from agentmemory.core.wiki import WIKI_TITLES, parse_knowledge_xml, parse_lint_xml, parse_wiki_consolidation_xml, parse_wiki_update_xml
from agentmemory.providers import LLMProvider
from agentmemory.state import StateKV
from agentmemory.state.schema import KV
from agentmemory.version import __version__


GOVERNANCE_SCHEMA_VERSION = 2


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
        project = self._resolve_project_record(request.cwd, request.project, request.projectId)
        observation = ObservationRecord(
            id=generate_id("obs"),
            type=request.type,
            content=request.content,
            source=request.source,
            language=request.language,
            project=project.name,
            projectId=project.id,
            cwd=project.root,
            files=request.files,
            concepts=request.concepts,
            createdAt=now,
        )

        self.kv.set(KV.observations(project.id), observation.id, observation.model_dump())
        self._enqueue_wiki_job([f"observation:{observation.id}"])
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
                details={"projectId": project.id, "type": observation.type},
            ),
        )
        processing_job = None
        summary = None
        memory_candidates: list[MemoryCandidateRecord] = []
        if self.llm:
            processing_job = create_pending_job(observation, now)
            self.kv.set(KV.llm_processing_jobs, processing_job.id, processing_job.model_dump())

        return ObserveResponse(
            observationId=observation.id,
            observation=observation,
            processingJob=processing_job,
            summary=summary,
            memoryCandidates=memory_candidates,
        )

    def remember(self, request: RememberRequest) -> RememberResponse:
        now = utc_now_iso()
        project = self._resolve_project_record(project=request.project, project_id=request.projectId) if request.scope == "project" else None
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
            scope=request.scope,
            project=project.name if project else request.project,
            projectId=project.id if project else request.projectId,
            createdAt=now,
        )
        self.kv.set(KV.memories, memory.id, memory.model_dump())
        self._enqueue_wiki_job([f"memory:{memory.id}"])
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

    def list_projects(self) -> list[ProjectRecord]:
        items = [ProjectRecord.model_validate(item) for item in self.kv.list(KV.projects)]
        return sorted(items, key=lambda item: item.updatedAt)

    def get_project(self, project_id: str) -> ProjectRecord | None:
        raw = self.kv.get(KV.projects, project_id)
        return ProjectRecord.model_validate(raw) if raw else None

    def list_memories(self) -> list[MemoryRecord]:
        items = [MemoryRecord.model_validate(item) for item in self.kv.list(KV.memories)]
        return sorted(items, key=lambda item: item.createdAt)

    def list_observations(self) -> list[ObservationRecord]:
        observations: list[ObservationRecord] = []
        for project in self.list_projects():
            observations.extend(
                ObservationRecord.model_validate(item)
                for item in self.kv.list(KV.observations(project.id))
            )
        return sorted({item.id: item for item in observations}.values(), key=lambda item: item.createdAt)

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

    def list_wiki_pages(self) -> list[WikiPageRecord]:
        items = [WikiPageRecord.model_validate(item) for item in self.kv.list(KV.wiki_pages)]
        return sorted(items, key=lambda item: item.updatedAt)

    def list_knowledge(self) -> list[KnowledgeRecord]:
        items = [KnowledgeRecord.model_validate(item) for item in self.kv.list(KV.knowledge)]
        return sorted(items, key=lambda item: item.updatedAt)

    def list_insights(self) -> list[InsightRecord]:
        items = [InsightRecord.model_validate(item) for item in self.kv.list(KV.insights)]
        return sorted(items, key=lambda item: item.updatedAt)

    def list_wiki_jobs(self) -> list[WikiUpdateJobRecord]:
        items = [WikiUpdateJobRecord.model_validate(item) for item in self.kv.list(KV.wiki_update_jobs)]
        return sorted(items, key=lambda item: item.createdAt)

    def list_pinned_memory(self, scope: MemoryScope | None = None, project_id: str | None = None) -> list[PinnedMemoryRecord]:
        items = [PinnedMemoryRecord.model_validate(item) for item in self.kv.list(KV.pinned_memory)]
        filtered = [
            item
            for item in items
            if (scope is None or item.scope == scope)
            and (project_id is None or item.projectId == project_id)
        ]
        return sorted(filtered, key=lambda item: (item.priority, item.updatedAt), reverse=True)

    def list_project_profiles(self) -> list[ProjectProfileRecord]:
        items = [ProjectProfileRecord.model_validate(item) for item in self.kv.list(KV.project_profiles)]
        return sorted(items, key=lambda item: item.updatedAt)

    def project_profile(self, project_id: str) -> ProjectProfileRecord | None:
        raw = self.kv.get(KV.project_profiles, project_id)
        return ProjectProfileRecord.model_validate(raw) if raw else None

    def pin_memory(self, request: PinMemoryRequest) -> PinMemoryResponse:
        now = utc_now_iso()
        project = self._resolve_project_record(project=request.project, project_id=request.projectId) if request.scope == "project" else None
        pinned = PinnedMemoryRecord(
            id=generate_id("pin"),
            scope=request.scope,
            project=project.name if project else None,
            projectId=project.id if project else None,
            content=request.content,
            sourceIds=request.sourceIds,
            priority=request.priority,
            confidence=request.confidence,
            createdAt=now,
            updatedAt=now,
        )
        self.kv.set(KV.pinned_memory, pinned.id, pinned.model_dump())
        return PinMemoryResponse(pinned=pinned)

    def disable_pinned_memory(self, pin_id: str) -> PinnedMemoryRecord:
        raw = self.kv.get(KV.pinned_memory, pin_id)
        if not raw:
            raise ValueError(f"pinned memory not found: {pin_id}")
        pinned = PinnedMemoryRecord.model_validate(raw)
        pinned.enabled = False
        pinned.updatedAt = utc_now_iso()
        self.kv.set(KV.pinned_memory, pinned.id, pinned.model_dump())
        return pinned

    def delete_pinned_memory(self, pin_id: str) -> bool:
        return self.kv.delete(KV.pinned_memory, pin_id)

    def update_project_profile(self, request: ProjectProfileUpdateRequest) -> ProjectProfileUpdateResponse:
        if not self.llm or not hasattr(self.llm, "update_project_profile"):
            raise RuntimeError("project profile update requires an llm provider")
        project = self._resolve_project_record(request.cwd, request.project, request.projectId)
        existing = self.project_profile(project.id)
        evidence = self._project_profile_evidence(project.id, request.limit)
        raw = self.llm.update_project_profile(project.model_dump(), existing.model_dump() if existing else None, evidence)  # type: ignore[union-attr]
        parsed = _parse_project_profile_text(raw)
        now = utc_now_iso()
        profile = ProjectProfileRecord(
            id=project.id,
            projectId=project.id,
            project=project.name,
            content=parsed["content"],
            goals=parsed["goals"],
            techStack=parsed["techStack"],
            keyFiles=parsed["keyFiles"],
            commands=parsed["commands"],
            conventions=parsed["conventions"],
            risks=parsed["risks"],
            sourceIds=_dedupe_strings([str(item.get("sourceId")) for item in evidence if item.get("sourceId")]),
            confidence=parsed["confidence"],
            createdAt=existing.createdAt if existing else now,
            updatedAt=now,
        )
        self.kv.set(KV.project_profiles, project.id, profile.model_dump())
        return ProjectProfileUpdateResponse(project=project, profile=profile)

    def process_wiki_updates(self, request: WikiUpdateRequest | None = None) -> WikiUpdateResponse:
        if not self.llm:
            raise RuntimeError("llm provider is not configured")
        request = request or WikiUpdateRequest()
        limit = request.limit if request else 10
        pending = [
            WikiUpdateJobRecord.model_validate(item)
            for item in self.kv.list(KV.wiki_update_jobs)
            if item.get("status") == "pending"
        ]
        jobs: list[WikiUpdateJobRecord] = []
        pages: list[WikiPageRecord] = []
        knowledge: list[KnowledgeRecord] = []
        for job in sorted(pending, key=lambda item: item.createdAt)[:limit]:
            if request.project or request.projectId:
                project = self._resolve_project_record(project=request.project, project_id=request.projectId)
                job.project = project.name
                job.projectId = project.id
                job.scope = request.scope
            processed, page, distilled = self._process_wiki_job(job)
            jobs.append(processed)
            if page:
                pages.append(page)
            knowledge.extend(distilled)
        return WikiUpdateResponse(jobs=jobs, pages=pages, knowledge=_unique_knowledge_records(knowledge))

    def retry_failed_wiki_jobs(self, limit: int = 10) -> int:
        failed = [
            WikiUpdateJobRecord.model_validate(item)
            for item in self.kv.list(KV.wiki_update_jobs)
            if item.get("status") == "failed"
        ]
        count = 0
        for job in sorted(failed, key=lambda item: item.updatedAt)[:limit]:
            job.status = "pending"
            job.updatedAt = utc_now_iso()
            job.lastError = None
            self.kv.set(KV.wiki_update_jobs, job.id, job.model_dump())
            count += 1
        return count

    def merge_pending_wiki_jobs(self) -> int:
        pending = [
            WikiUpdateJobRecord.model_validate(item)
            for item in self.kv.list(KV.wiki_update_jobs)
            if item.get("status") == "pending"
        ]
        merged = 0
        by_topic: dict[WikiTopic | None, WikiUpdateJobRecord] = {}
        for job in sorted(pending, key=lambda item: item.createdAt):
            existing = by_topic.get(job.topic)
            if existing is None:
                by_topic[job.topic] = job
                continue
            if set(existing.sourceIds).isdisjoint(job.sourceIds):
                continue
            existing.sourceIds = _dedupe_strings([*existing.sourceIds, *job.sourceIds])
            existing.updatedAt = utc_now_iso()
            self.kv.set(KV.wiki_update_jobs, existing.id, existing.model_dump())
            self.kv.delete(KV.wiki_update_jobs, job.id)
            merged += 1
        return merged

    def rebuild_wiki(self, request: WikiRebuildRequest) -> WikiUpdateResponse:
        topics: list[WikiTopic]
        if request.all:
            topics = list(WIKI_TOPICS)
        elif request.topic:
            topics = [request.topic]
        else:
            raise ValueError("wiki rebuild requires topic or all=true")
        source_ids = [
            *(f"observation:{item.id}" for item in self.list_observations()),
            *(f"memory:{item.id}" for item in self.list_memories()),
            *(f"summary:{item.id}" for item in self.list_summaries()),
        ]
        source_ids = self._uncovered_wiki_source_ids(source_ids)
        project = self._resolve_project_record(project=request.project, project_id=request.projectId) if request.scope == "project" else None
        jobs = [
            self._enqueue_wiki_job(
                source_ids,
                topic=topic,
                scope=request.scope,
                project=project.name if project else None,
                project_id=project.id if project else None,
            )
            for topic in topics
        ]
        if not self.llm:
            return WikiUpdateResponse(jobs=jobs, pages=[])
        processed: list[WikiUpdateJobRecord] = []
        pages: list[WikiPageRecord] = []
        knowledge: list[KnowledgeRecord] = []
        for job in jobs:
            result, page, distilled = self._process_wiki_job(job)
            processed.append(result)
            if page:
                pages.append(page)
            knowledge.extend(distilled)
        return WikiUpdateResponse(jobs=processed, pages=pages, knowledge=_unique_knowledge_records(knowledge))

    async def run_wiki_worker(self, stop_event: asyncio.Event, interval_seconds: float = 10.0) -> None:
        while not stop_event.is_set():
            await asyncio.to_thread(self.process_wiki_updates, WikiUpdateRequest(limit=5))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                pass

    async def run_maintenance_worker(
        self,
        stop_event: asyncio.Event,
        interval_seconds: float = 10.0,
        limit: int = 25,
    ) -> None:
        while not stop_event.is_set():
            await asyncio.to_thread(self.run_maintenance, MaintenanceRunRequest(limit=limit))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                pass

    def list_index_jobs(self) -> list[IndexJobRecord]:
        items = [IndexJobRecord.model_validate(item) for item in self.kv.list(KV.index_jobs)]
        return sorted(items, key=lambda item: item.startedAt)

    def export_data(self, source: str = "cli") -> GovernanceExport:
        now = utc_now_iso()
        projects = self.list_projects()
        observations = self.list_observations()
        memories = self.list_memories()
        summaries = self.list_summaries()
        memory_candidates = self.list_memory_candidates()
        llm_processing_jobs = self.list_llm_processing_jobs()
        knowledge = self.list_knowledge()
        insights = self.list_insights()
        index_jobs = self.list_index_jobs()
        audit = AuditRecord(
            id=generate_id("aud"),
            action="export",
            targetType="governance",
            targetId="agentmemory",
            source=source,
            timestamp=now,
            details={
                "projects": len(projects),
                "observations": len(observations),
                "memories": len(memories),
                "summaries": len(summaries),
                "memoryCandidates": len(memory_candidates),
                "llmProcessingJobs": len(llm_processing_jobs),
                "knowledge": len(knowledge),
                "insights": len(insights),
                "indexJobs": len(index_jobs),
            },
        )
        self._record_audit(audit)
        return GovernanceExport(
            version=__version__,
            schemaVersion=GOVERNANCE_SCHEMA_VERSION,
            exportedAt=now,
            projects=projects,
            projectProfiles=self.list_project_profiles(),
            pinnedMemory=self.list_pinned_memory(),
            observations=observations,
            memories=memories,
            summaries=summaries,
            memoryCandidates=memory_candidates,
            llmProcessingJobs=llm_processing_jobs,
            knowledge=knowledge,
            insights=insights,
            wikiPages=self.list_wiki_pages(),
            wikiUpdateJobs=self.list_wiki_jobs(),
            indexJobs=index_jobs,
            audit=self.list_audit(),
        )

    def import_data(self, request: GovernanceImportRequest) -> GovernanceImportResponse:
        payload = request.payload
        schema_version = _governance_schema_version(payload)
        imported: dict[str, int] = {}
        skipped: dict[str, int] = {}
        errors: list[str] = []

        self._import_collection(KV.projects, payload.get("projects", []), ProjectRecord, imported, skipped, errors, "projects")
        self._import_collection(
            KV.project_profiles,
            payload.get("projectProfiles", []),
            ProjectProfileRecord,
            imported,
            skipped,
            errors,
            "projectProfiles",
        )
        self._import_collection(
            KV.pinned_memory,
            payload.get("pinnedMemory", []),
            PinnedMemoryRecord,
            imported,
            skipped,
            errors,
            "pinnedMemory",
        )
        self._import_observations(payload.get("observations", []), imported, skipped, errors)
        self._import_collection(KV.memories, payload.get("memories", []), MemoryRecord, imported, skipped, errors, "memories")
        self._import_collection(KV.summaries, payload.get("summaries", []), SummaryRecord, imported, skipped, errors, "summaries")
        self._import_collection(
            KV.memory_candidates,
            payload.get("memoryCandidates", []),
            MemoryCandidateRecord,
            imported,
            skipped,
            errors,
            "memoryCandidates",
        )
        self._import_collection(
            KV.llm_processing_jobs,
            payload.get("llmProcessingJobs", []),
            LLMProcessingJobRecord,
            imported,
            skipped,
            errors,
            "llmProcessingJobs",
        )
        self._import_collection(KV.knowledge, payload.get("knowledge", []), KnowledgeRecord, imported, skipped, errors, "knowledge")
        self._import_collection(KV.insights, payload.get("insights", []), InsightRecord, imported, skipped, errors, "insights")
        self._import_collection(KV.wiki_pages, payload.get("wikiPages", []), WikiPageRecord, imported, skipped, errors, "wikiPages")
        self._import_collection(
            KV.wiki_update_jobs,
            payload.get("wikiUpdateJobs", []),
            WikiUpdateJobRecord,
            imported,
            skipped,
            errors,
            "wikiUpdateJobs",
        )
        self._import_collection(KV.index_jobs, payload.get("indexJobs", []), IndexJobRecord, imported, skipped, errors, "indexJobs")
        self._import_collection(KV.audit, payload.get("audit", []), AuditRecord, imported, skipped, errors, "audit")
        self._index_imported_data()

        now = utc_now_iso()
        audit = AuditRecord(
            id=generate_id("aud"),
            action="import",
            targetType="governance",
            targetId="agentmemory",
            source=request.source,
            timestamp=now,
            details={
                "schemaVersion": schema_version,
                "imported": imported,
                "skipped": skipped,
                "errors": errors[:20],
            },
        )
        self._record_audit(audit)
        return GovernanceImportResponse(
            schemaVersion=schema_version,
            imported=imported,
            skipped=skipped,
            errors=errors,
            auditId=audit.id,
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

    def _import_collection(
        self,
        scope: str,
        items: object,
        model,
        imported: dict[str, int],
        skipped: dict[str, int],
        errors: list[str],
        label: str,
    ) -> None:
        if not _is_list(items, label, errors):
            return
        for index, item in enumerate(items):
            try:
                record = model.model_validate(item)
                record_id = str(record.id)
            except Exception as exc:
                errors.append(f"{label}[{index}]: {exc}")
                continue
            if self.kv.get(scope, record_id) is not None:
                _increment(skipped, label)
                continue
            self.kv.set(scope, record_id, record.model_dump())
            _increment(imported, label)

    def _import_observations(
        self,
        items: object,
        imported: dict[str, int],
        skipped: dict[str, int],
        errors: list[str],
    ) -> None:
        label = "observations"
        if not _is_list(items, label, errors):
            return
        for index, item in enumerate(items):
            try:
                observation = ObservationRecord.model_validate(item)
            except Exception as exc:
                errors.append(f"{label}[{index}]: {exc}")
                continue
            project_id = observation.projectId or (
                self._resolve_project_record(cwd=observation.cwd, project=observation.project).id
                if observation.project or observation.cwd
                else "global"
            )
            scope = KV.observations(project_id)
            if self.kv.get(scope, observation.id) is not None:
                _increment(skipped, label)
                continue
            self.kv.set(scope, observation.id, observation.model_dump())
            _increment(imported, label)

    def _index_imported_data(self) -> None:
        if not self.search_service:
            return
        observations_by_id = {observation.id: observation for observation in self.list_observations()}
        for observation in observations_by_id.values():
            self.search_service.index_document(observation_document(observation))
        for memory in self.list_memories():
            self.search_service.index_document(memory_document(memory))
        for summary in self.list_summaries():
            observation = observations_by_id.get(summary.observationId) if summary.observationId else None
            self.search_service.index_document(summary_document(summary, observation))
        for knowledge in self.list_knowledge():
            if not knowledge.deleted:
                self.search_service.index_document(knowledge_document(knowledge))
        for insight in self.list_insights():
            self.search_service.index_document(insight_document(insight))
        for page in self.list_wiki_pages():
            self.search_service.index_document(wiki_page_document(page))

    def search(self, request):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.search(request)

    def smart_search(self, request):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.smart_search(request)

    def context(self, request: ContextRequest):
        if not self.search_service:
            raise RuntimeError("search service is not configured")
        return self.search_service.context(request)

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

    def consolidate_wiki(self, request: WikiConsolidateRequest | None = None) -> WikiConsolidateResponse:
        request = request or WikiConsolidateRequest()
        if request.scope == "project" and (request.project or request.projectId):
            project = self._resolve_project_record(project=request.project, project_id=request.projectId)
            request.project = project.name
            request.projectId = project.id
        source_items = self._consolidation_sources(request.limit, request.project)
        if len(source_items) < request.minEvidence:
            return WikiConsolidateResponse(skipped={"reason": "insufficient evidence", "sources": len(source_items)})
        if not self.llm or not hasattr(self.llm, "consolidate_wiki"):
            raise RuntimeError("wiki consolidation requires an llm provider")
        return self._consolidate_wiki_with_llm(request, source_items)

    def recall_lessons(self, request: LessonRecallRequest) -> LessonRecallResponse:
        terms = _query_terms(request.query)
        lessons = [
            item
            for item in self.list_knowledge()
            if item.kind == "lesson"
            and not item.deleted
            and (item.confidence or 0.0) >= request.minConfidence
            and (request.project is None or item.project == request.project)
        ]
        scored = sorted(
            lessons,
            key=lambda item: (
                _term_overlap(" ".join([item.content, " ".join(item.concepts)]), terms),
                item.confidence or 0.0,
                item.updatedAt,
            ),
            reverse=True,
        )
        return LessonRecallResponse(lessons=[item for item in scored if not terms or _term_overlap(item.content, terms) > 0][: request.limit])

    def strengthen_lesson(self, lesson_id: str) -> KnowledgeRecord:
        raw = self.kv.get(KV.knowledge, lesson_id)
        if raw is None:
            raise ValueError(f"lesson not found: {lesson_id}")
        lesson = KnowledgeRecord.model_validate(raw)
        if lesson.kind != "lesson":
            raise ValueError(f"knowledge is not a lesson: {lesson_id}")
        return self._reinforce_knowledge(lesson, [], utc_now_iso())

    def decay_lessons(self, limit: int = 100) -> dict[str, object]:
        now = utc_now_iso()
        decayed = 0
        deleted = 0
        for lesson in [item for item in self.list_knowledge() if item.kind == "lesson" and not item.deleted][:limit]:
            baseline = lesson.lastDecayedAt or lesson.lastReinforcedAt or lesson.updatedAt
            days = _days_between(baseline, now)
            if days < 7:
                continue
            lesson.confidence = max(0.05, round((lesson.confidence or 0.5) - lesson.decayRate * (days // 7), 3))
            lesson.lastDecayedAt = now
            lesson.updatedAt = now
            if lesson.confidence <= 0.1 and lesson.reinforcements == 0:
                lesson.deleted = True
                deleted += 1
            else:
                decayed += 1
            self.kv.set(KV.knowledge, lesson.id, lesson.model_dump())
            if self.search_service:
                if lesson.deleted:
                    self.search_service.delete_document("knowledge", lesson.id)
                else:
                    self.search_service.index_document(knowledge_document(lesson))
        return {"decayed": decayed, "deleted": deleted}

    def create_crystal(self, request: CrystalCreateRequest) -> CrystalCreateResponse:
        now = utc_now_iso()
        source_group = _knowledge_source_group(request.sourceIds)
        evidence = self._wiki_evidence(request.sourceIds)
        content = _crystal_content(evidence, request.sourceIds)
        crystal = self._upsert_knowledge(
            kind="crystal",
            content=content,
            source_ids=request.sourceIds,
            concepts=_concepts_from_evidence(evidence),
            confidence=0.75,
            now=now,
            source_group=source_group,
            project=request.project,
            scope="project" if request.project else "global",
        )
        lesson = self._upsert_knowledge(
            kind="lesson",
            content=f"Preserve the outcome from this source group: {content}",
            source_ids=[f"knowledge:{crystal.id}", *request.sourceIds],
            concepts=crystal.concepts,
            confidence=0.65,
            now=now,
            project=request.project,
            scope="project" if request.project else "global",
        )
        return CrystalCreateResponse(crystal=crystal, lessons=[lesson])

    def reflect_wiki(self, request: WikiReflectRequest | None = None) -> WikiReflectResponse:
        request = request or WikiReflectRequest()
        knowledge = [
            item
            for item in self.list_knowledge()
            if not item.deleted and (request.project is None or item.project in (None, request.project))
        ][: request.limit]
        groups = self._group_sources_by_concepts(
            [
                {
                    "sourceId": f"knowledge:{item.id}",
                    "content": item.content,
                    "concepts": item.concepts or [item.kind],
                }
                for item in knowledge
            ],
        )
        insights: list[InsightRecord] = []
        reinforced = 0
        now = utc_now_iso()
        for concept, items in groups.items():
            if len(items) < 2:
                continue
            source_ids = _dedupe_strings([str(item["sourceId"]) for item in items])
            content = self._consolidated_content(concept, items)
            title = f"{concept} insight"
            fingerprint = _knowledge_fingerprint("insight", content, None)
            existing = self._insight_by_fingerprint(fingerprint)
            if existing:
                existing.reinforcements += 1
                existing.lastReinforcedAt = now
                existing.updatedAt = now
                existing.sourceIds = _dedupe_strings([*existing.sourceIds, *source_ids])
                self.kv.set(KV.insights, existing.id, existing.model_dump())
                if self.search_service:
                    self.search_service.index_document(insight_document(existing))
                insights.append(existing)
                reinforced += 1
                continue
            insight = InsightRecord(
                id=generate_id("ins"),
                title=title,
                content=content,
                sourceIds=source_ids,
                concepts=[concept],
                confidence=min(0.9, 0.55 + len(items) * 0.08),
                fingerprint=fingerprint,
                project=request.project,
                createdAt=now,
                updatedAt=now,
            )
            self.kv.set(KV.insights, insight.id, insight.model_dump())
            if self.search_service:
                self.search_service.index_document(insight_document(insight))
            insights.append(insight)
        return WikiReflectResponse(insights=insights, reinforced=reinforced, skipped={"groups": len(groups)})

    def lint_wiki(self) -> WikiLintResponse:
        if not self.llm or not hasattr(self.llm, "lint_wiki"):
            raise RuntimeError("wiki lint requires an llm provider")
        raw = self.llm.lint_wiki(self._existing_wiki_records_for_llm())  # type: ignore[union-attr]
        issues = [WikiLintIssue.model_validate(item) for item in parse_lint_xml(raw)]
        issues.extend(self._deterministic_wiki_lint_issues())
        return WikiLintResponse(issues=issues)

    def _deterministic_wiki_lint_issues(self) -> list[WikiLintIssue]:
        issues: list[WikiLintIssue] = []
        for item in self.list_knowledge():
            if not item.sourceIds:
                issues.append(
                    WikiLintIssue(
                        type="missing_source",
                        severity="warning",
                        message=f"Knowledge {item.id} has no source ids.",
                        sourceIds=[f"knowledge:{item.id}"],
                        suggestedAction="Re-file or consolidate this knowledge with provenance.",
                    ),
                )
            if item.confidence is not None and item.confidence < 0.25 and not item.deleted:
                issues.append(
                    WikiLintIssue(
                        type="low_confidence",
                        severity="info",
                        message=f"Knowledge {item.id} has low confidence.",
                        sourceIds=[f"knowledge:{item.id}", *item.sourceIds],
                        suggestedAction="Strengthen with more evidence or let lesson decay mark it inactive.",
                    ),
                )
            if _contains_contradiction_marker(item.content):
                issues.append(
                    WikiLintIssue(
                        type="contradiction",
                        severity="warning",
                        message=f"Knowledge {item.id} may contain a contradiction marker.",
                        sourceIds=[f"knowledge:{item.id}", *item.sourceIds],
                        suggestedAction="Review and file a corrected answer or rerun consolidation.",
                    ),
                )
        for page in self.list_wiki_pages():
            if not page.sourceIds:
                issues.append(
                    WikiLintIssue(
                        type="orphan",
                        severity="warning",
                        message=f"Wiki page {page.id} has no source ids.",
                        sourceIds=[f"wikiPage:{page.id}"],
                        suggestedAction="Rebuild the page from sourced evidence.",
                    ),
                )
        return issues

    def file_wiki_answer(self, request: WikiFileAnswerRequest) -> WikiFileAnswerResponse:
        now = utc_now_iso()
        if request.kind == "insight":
            insight = self._upsert_insight(
                title=request.query[:80],
                content=request.content,
                source_ids=request.sourceIds,
                concepts=request.concepts,
                confidence=request.confidence,
                now=now,
                project=request.project,
                scope="project" if request.project else "global",
                query=request.query,
            )
            return WikiFileAnswerResponse(record=insight)
        record = self._upsert_knowledge(
            kind=request.kind,
            content=request.content,
            source_ids=request.sourceIds,
            concepts=request.concepts,
            confidence=request.confidence,
            now=now,
            source_group=_knowledge_source_group(request.sourceIds) if request.kind == "crystal" and request.sourceIds else None,
            project=request.project,
            scope="project" if request.project else "global",
            query=request.query,
        )
        return WikiFileAnswerResponse(record=record)

    def run_maintenance(self, request: MaintenanceRunRequest | None = None) -> MaintenanceRunResponse:
        request = request or MaintenanceRunRequest()
        errors: list[str] = []
        index_result: dict[str, object] = {}
        wiki_result: dict[str, object] = {}
        llm_result: dict[str, object] = {}
        page_result: dict[str, object] = {"compressed": 0}

        try:
            if self.search_service:
                index_result = self.search_service.repair()
        except Exception as exc:
            errors.append(f"index: {exc}")
            index_result = {"documents": 0, "jobs": []}

        try:
            llm_result = self.retry_failed_llm_processing(request.limit)
        except Exception as exc:
            errors.append(f"llm: {exc}")
            llm_result = {"jobs": []}

        try:
            merged = self.merge_pending_wiki_jobs()
            retried = self.retry_failed_wiki_jobs(request.limit) if request.retryFailed else 0
            wiki = self.process_wiki_updates(WikiUpdateRequest(limit=request.limit)) if self.llm else WikiUpdateResponse()
            profiles = []
            if self.llm:
                for project in self.list_projects()[:5]:
                    try:
                        profiles.append(
                            self.update_project_profile(
                                ProjectProfileUpdateRequest(
                                    project=project.name,
                                    projectId=project.id,
                                    cwd=project.root,
                                    limit=request.limit,
                                ),
                            ).profile.model_dump(),
                        )
                    except Exception as exc:
                        errors.append(f"profile:{project.id}: {exc}")
            wiki_result = {
                "merged": merged,
                "retried": retried,
                "jobs": [job.model_dump() for job in wiki.jobs],
                "pages": [page.model_dump() for page in wiki.pages],
                "knowledge": [item.model_dump() for item in wiki.knowledge],
                "projectProfiles": profiles,
            }
        except Exception as exc:
            errors.append(f"wiki: {exc}")
            wiki_result = {"merged": 0, "retried": 0, "jobs": [], "pages": [], "knowledge": []}

        return MaintenanceRunResponse(
            index=index_result,
            wiki=wiki_result,
            llm=llm_result,
            pageCompression=page_result,
            errors=errors,
        )

    def retry_failed_llm_processing(self, limit: int = 25) -> dict[str, object]:
        if not self.llm:
            return {"jobs": []}
        pending_or_failed = [
            LLMProcessingJobRecord.model_validate(item)
            for item in self.kv.list(KV.llm_processing_jobs)
            if item.get("status") in {"pending", "failed"}
        ]
        jobs: list[LLMProcessingJobRecord] = []
        for job in sorted(pending_or_failed, key=lambda item: item.startedAt)[:limit]:
            observation = self._observation_by_id(job.observationId)
            if observation is None:
                job.attempts += 1
                job.lastError = "observation not found"
                job.finishedAt = utc_now_iso()
                self.kv.set(KV.llm_processing_jobs, job.id, job.model_dump())
                jobs.append(job)
                continue
            job.status = "running"
            job.attempts += 1
            job.lastError = None
            self.kv.set(KV.llm_processing_jobs, job.id, job.model_dump())
            job, summary, candidates = process_observation(observation=observation, llm=self.llm, job=job)
            if summary:
                self.kv.set(KV.summaries, summary.id, summary.model_dump())
                self._enqueue_wiki_job([f"summary:{summary.id}"])
                if self.search_service:
                    self.search_service.index_document(summary_document(summary, observation))
            for candidate in candidates:
                self.kv.set(KV.memory_candidates, candidate.id, candidate.model_dump())
            self.kv.set(KV.llm_processing_jobs, job.id, job.model_dump())
            self._record_audit(
                AuditRecord(
                    id=generate_id("aud"),
                    action="llm_processing_done" if job.status == "done" else "llm_processing_failed",
                    targetType="llm_processing_job",
                    targetId=job.id,
                    source="maintenance",
                    timestamp=job.finishedAt or utc_now_iso(),
                    details={
                        "observationId": observation.id,
                        "summaryId": job.summaryId,
                        "candidateIds": job.candidateIds,
                        "lastError": job.lastError,
                    },
                ),
            )
            jobs.append(job)
        return {"jobs": [job.model_dump() for job in jobs]}

    def _observation_by_id(self, observation_id: str) -> ObservationRecord | None:
        for observation in self.list_observations():
            if observation.id == observation_id:
                return observation
        return None

    def _resolve_project_record(
        self,
        cwd: str | None = None,
        project: str | None = None,
        project_id: str | None = None,
    ) -> ProjectRecord:
        candidate = resolve_project_identity(cwd=cwd, project=project, project_id=project_id)
        existing = self.kv.get(KV.projects, candidate.id)
        record = resolve_project_identity(
            cwd=cwd or candidate.root,
            project=project or candidate.name,
            project_id=project_id or candidate.id,
            existing=ProjectRecord.model_validate(existing) if existing else None,
        )
        self.kv.set(KV.projects, record.id, record.model_dump())
        return record

    def _record_audit(self, record: AuditRecord) -> None:
        self.kv.set(KV.audit, record.id, record.model_dump())

    def _enqueue_wiki_job(
        self,
        source_ids: list[str],
        topic: WikiTopic | None = None,
        scope: MemoryScope = "project",
        project: str | None = None,
        project_id: str | None = None,
    ) -> WikiUpdateJobRecord:
        now = utc_now_iso()
        job = WikiUpdateJobRecord(
            id=generate_id("wiki_job"),
            sourceIds=_dedupe_strings(source_ids),
            topic=topic,
            scope=scope,
            project=project,
            projectId=project_id,
            status="pending",
            createdAt=now,
            updatedAt=now,
        )
        self.kv.set(KV.wiki_update_jobs, job.id, job.model_dump())
        return job

    def _process_wiki_job(
        self,
        job: WikiUpdateJobRecord,
    ) -> tuple[WikiUpdateJobRecord, WikiPageRecord | None, list[KnowledgeRecord]]:
        now = utc_now_iso()
        job.status = "running"
        job.attempts += 1
        job.updatedAt = now
        job.lastError = None
        self.kv.set(KV.wiki_update_jobs, job.id, job.model_dump())
        try:
            topic = job.topic or self._infer_wiki_topic(job.sourceIds)
            existing = self._wiki_page_by_topic(topic, job.scope, job.projectId)
            title = existing.title if existing else WIKI_TITLES[topic]
            evidence = self._wiki_evidence(job.sourceIds)
            distilled = self._distill_knowledge(job, evidence) if _should_distill_wiki_job(job) else []
            wiki_evidence = [*evidence, *[{"sourceId": f"knowledge:{item.id}", **item.model_dump()} for item in distilled]]
            raw = self.llm.update_wiki(topic, title, existing.content if existing else "", wiki_evidence)  # type: ignore[union-attr]
            proposal = parse_wiki_update_xml(raw)
            if proposal is None:
                raise ValueError("invalid wiki update proposal")
            page = self._apply_wiki_proposal(job, proposal, existing)
            job.status = "applied"
            job.topic = page.topic
            job.proposal = proposal
            job.updatedAt = page.updatedAt
            job.lastError = None
            self.kv.set(KV.wiki_update_jobs, job.id, job.model_dump())
            return job, page, distilled
        except Exception as exc:
            job.status = "failed"
            job.lastError = str(exc)
            job.updatedAt = utc_now_iso()
            self.kv.set(KV.wiki_update_jobs, job.id, job.model_dump())
            return job, None, []

    def _distill_knowledge(self, job: WikiUpdateJobRecord, evidence: list[dict[str, object]]) -> list[KnowledgeRecord]:
        if not evidence:
            return []
        raw = self.llm.distill_knowledge(evidence)  # type: ignore[union-attr]
        proposals = _select_distilled_knowledge(parse_knowledge_xml(raw))
        records: list[KnowledgeRecord] = []
        now = utc_now_iso()
        source_group = _knowledge_source_group(job.sourceIds)
        for proposal in proposals:
            kind = proposal["kind"]
            content = str(proposal["content"])
            fingerprint = _knowledge_fingerprint(str(kind), content, source_group if kind == "crystal" else None)
            existing = self._knowledge_by_fingerprint(fingerprint)
            if existing:
                updated = self._reinforce_knowledge(existing, job.sourceIds, now)
                records.append(updated)
                continue
            record = KnowledgeRecord(
                id=generate_id("know"),
                kind=kind,
                content=content,
                sourceIds=job.sourceIds,
                concepts=proposal.get("concepts") if isinstance(proposal.get("concepts"), list) else [],
                files=proposal.get("files") if isinstance(proposal.get("files"), list) else [],
                confidence=proposal.get("confidence") if isinstance(proposal.get("confidence"), float) else None,
                fingerprint=fingerprint,
                reinforcements=1 if kind == "lesson" else 0,
                lastReinforcedAt=now if kind == "lesson" else None,
                sourceGroup=source_group if kind == "crystal" else None,
                scope=job.scope,
                project=job.project,
                projectId=job.projectId,
                createdAt=now,
                updatedAt=now,
            )
            self.kv.set(KV.knowledge, record.id, record.model_dump())
            if self.search_service:
                self.search_service.index_document(knowledge_document(record))
            self._record_audit(
                AuditRecord(
                    id=generate_id("aud"),
                    action="knowledge_distill",
                    targetType="knowledge",
                    targetId=record.id,
                    source="llm",
                    timestamp=now,
                    details={"jobId": job.id, "kind": record.kind, "sourceIds": record.sourceIds},
                ),
            )
            records.append(record)
        return records

    def _knowledge_by_fingerprint(self, fingerprint: str) -> KnowledgeRecord | None:
        for item in self.list_knowledge():
            if item.fingerprint == fingerprint:
                return item
        return None

    def _reinforce_knowledge(self, existing: KnowledgeRecord, source_ids: list[str], now: str) -> KnowledgeRecord:
        existing.sourceIds = _dedupe_strings([*existing.sourceIds, *source_ids])
        existing.updatedAt = now
        existing.deleted = False
        if existing.kind == "lesson":
            existing.reinforcements += 1
            existing.lastReinforcedAt = now
            if existing.confidence is not None:
                existing.confidence = min(0.99, round(existing.confidence + 0.03, 3))
        self.kv.set(KV.knowledge, existing.id, existing.model_dump())
        if self.search_service:
            self.search_service.index_document(knowledge_document(existing))
        return existing

    def _upsert_knowledge(
        self,
        kind: str,
        content: str,
        source_ids: list[str],
        concepts: list[str],
        confidence: float | None,
        now: str,
        source_group: str | None = None,
        project: str | None = None,
        project_id: str | None = None,
        scope: MemoryScope = "global",
        query: str | None = None,
    ) -> KnowledgeRecord:
        fingerprint = _knowledge_fingerprint(kind, content, source_group if kind == "crystal" else None)
        existing = self._knowledge_by_fingerprint(fingerprint)
        if existing:
            existing.concepts = _dedupe_strings([*existing.concepts, *concepts])
            existing.scope = scope or existing.scope
            existing.project = project or existing.project
            existing.projectId = project_id or existing.projectId
            existing.query = query or existing.query
            if confidence is not None:
                existing.confidence = max(existing.confidence or 0.0, confidence)
            return self._reinforce_knowledge(existing, source_ids, now)
        record = KnowledgeRecord(
            id=generate_id("know"),
            kind=kind,  # type: ignore[arg-type]
            content=content,
            sourceIds=_dedupe_strings(source_ids),
            concepts=_dedupe_strings(concepts),
            files=[],
            confidence=confidence,
            fingerprint=fingerprint,
            reinforcements=1 if kind == "lesson" else 0,
            lastReinforcedAt=now if kind == "lesson" else None,
            scope=scope,
            project=project,
            projectId=project_id,
            query=query,
            sourceGroup=source_group,
            createdAt=now,
            updatedAt=now,
        )
        self.kv.set(KV.knowledge, record.id, record.model_dump())
        if self.search_service:
            self.search_service.index_document(knowledge_document(record))
        return record

    def _upsert_insight(
        self,
        title: str,
        content: str,
        source_ids: list[str],
        concepts: list[str],
        confidence: float | None,
        now: str,
        project: str | None = None,
        project_id: str | None = None,
        scope: MemoryScope = "global",
        query: str | None = None,
    ) -> InsightRecord:
        fingerprint = _knowledge_fingerprint("insight", content, None)
        existing = self._insight_by_fingerprint(fingerprint)
        if existing:
            existing.sourceIds = _dedupe_strings([*existing.sourceIds, *source_ids])
            existing.concepts = _dedupe_strings([*existing.concepts, *concepts])
            existing.reinforcements += 1
            existing.lastReinforcedAt = now
            existing.updatedAt = now
            existing.scope = scope or existing.scope
            existing.project = project or existing.project
            existing.projectId = project_id or existing.projectId
            existing.query = query or existing.query
            if confidence is not None:
                existing.confidence = max(existing.confidence or 0.0, confidence)
            self.kv.set(KV.insights, existing.id, existing.model_dump())
            if self.search_service:
                self.search_service.index_document(insight_document(existing))
            return existing
        insight = InsightRecord(
            id=generate_id("ins"),
            title=title,
            content=content,
            sourceIds=_dedupe_strings(source_ids),
            concepts=_dedupe_strings(concepts),
            confidence=confidence,
            fingerprint=fingerprint,
            scope=scope,
            project=project,
            projectId=project_id,
            query=query,
            createdAt=now,
            updatedAt=now,
        )
        self.kv.set(KV.insights, insight.id, insight.model_dump())
        if self.search_service:
            self.search_service.index_document(insight_document(insight))
        return insight

    def _insight_by_fingerprint(self, fingerprint: str) -> InsightRecord | None:
        for item in self.list_insights():
            if item.fingerprint == fingerprint:
                return item
        return None

    def _consolidate_wiki_with_llm(
        self,
        request: WikiConsolidateRequest,
        source_items: list[dict[str, object]],
    ) -> WikiConsolidateResponse:
        raw = self.llm.consolidate_wiki(source_items, self._existing_wiki_records_for_llm(request.limit, request.project))  # type: ignore[union-attr]
        parsed = parse_wiki_consolidation_xml(raw)
        now = utc_now_iso()
        semantic: list[KnowledgeRecord] = []
        procedural: list[KnowledgeRecord] = []
        default_source_ids = _dedupe_strings([str(item["sourceId"]) for item in source_items if item.get("sourceId")])
        for proposal in parsed["knowledge"]:
            kind = str(proposal["kind"])
            record = self._upsert_knowledge(
                kind=kind,
                content=str(proposal["content"]),
                source_ids=default_source_ids,
                concepts=proposal.get("concepts") if isinstance(proposal.get("concepts"), list) else [],
                confidence=proposal.get("confidence") if isinstance(proposal.get("confidence"), float) else None,
                now=now,
                project=request.project,
                project_id=request.projectId,
                scope="project" if request.project or request.projectId else "global",
            )
            if record.kind == "semantic":
                semantic.append(record)
            elif record.kind == "procedural":
                procedural.append(record)
        pages = [
            self._upsert_dynamic_wiki_page(
                page,
                default_source_ids,
                now,
                scope="project" if request.project else "global",
                project=request.project,
                project_id=request.projectId,
            )
            for page in parsed["pages"]
        ]
        issues = [WikiLintIssue.model_validate(item) for item in parsed["issues"]]
        return WikiConsolidateResponse(
            semantic=semantic,
            procedural=procedural,
            pages=pages,
            lintIssues=issues,
            skipped={"strategy": "llm", "sources": len(source_items), "existing": len(self._existing_wiki_records_for_llm(request.limit, request.project))},
        )

    def _upsert_dynamic_wiki_page(
        self,
        proposal: dict[str, object],
        default_source_ids: list[str],
        now: str,
        scope: MemoryScope = "global",
        project: str | None = None,
        project_id: str | None = None,
    ) -> WikiPageRecord:
        page_type = str(proposal.get("type") or "synthesis")
        slug = str(proposal.get("slug") or _knowledge_fingerprint(page_type, str(proposal.get("title", "")), None)[:24])
        topic = proposal.get("topic") if proposal.get("topic") in WIKI_TOPICS else "project_overview"
        existing = self._wiki_page_by_type_slug(page_type, slug, scope, project_id)
        source_ids = proposal.get("sourceIds") if isinstance(proposal.get("sourceIds"), list) else []
        page = WikiPageRecord(
            id=existing.id if existing else generate_id("wiki"),
            title=str(proposal.get("title") or slug),
            topic=topic,  # type: ignore[arg-type]
            type=page_type,  # type: ignore[arg-type]
            slug=slug,
            parentTopic=topic,  # type: ignore[arg-type]
            content=str(proposal.get("content") or ""),
            sourceIds=_dedupe_strings([*(existing.sourceIds if existing else []), *[str(item) for item in source_ids], *default_source_ids]),
            confidence=proposal.get("confidence") if isinstance(proposal.get("confidence"), float) else None,
            scope=scope,
            project=project,
            projectId=project_id,
            createdAt=existing.createdAt if existing else now,
            updatedAt=now,
        )
        self.kv.set(KV.wiki_pages, page.id, page.model_dump())
        if self.search_service:
            self.search_service.index_document(wiki_page_document(page))
        self._record_audit(
            AuditRecord(
                id=generate_id("aud"),
                action="wiki_update",
                targetType="wiki_page",
                targetId=page.id,
                source="llm",
                timestamp=now,
                details={"type": page.type, "slug": page.slug, "topic": page.topic, "sourceIds": page.sourceIds},
            ),
        )
        return page

    def _wiki_page_by_type_slug(
        self,
        page_type: str,
        slug: str,
        scope: MemoryScope | None = None,
        project_id: str | None = None,
    ) -> WikiPageRecord | None:
        for page in self.list_wiki_pages():
            if (
                page.type == page_type
                and page.slug == slug
                and (scope is None or page.scope == scope)
                and (project_id is None or page.projectId == project_id)
            ):
                return page
        return None

    def _existing_wiki_records_for_llm(self, limit: int = 50, project: str | None = None) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for item in self.list_knowledge():
            if item.deleted or (project is not None and item.project not in (None, project)):
                continue
            records.append({"recordType": "knowledge", **item.model_dump()})
        for item in self.list_insights():
            if project is not None and item.project not in (None, project):
                continue
            records.append({"recordType": "insight", **item.model_dump()})
        for item in self.list_wiki_pages():
            records.append({"recordType": "wikiPage", **item.model_dump()})
        return records[:limit]

    def _consolidation_sources(self, limit: int, project: str | None = None) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for summary in self.list_summaries():
            items.append(
                {
                    "sourceId": f"summary:{summary.id}",
                    "content": summary.content,
                    "concepts": [],
                    "project": None,
                },
            )
        for memory in self.list_memories():
            if project is None or memory.source == project or project in memory.concepts:
                items.append(
                    {
                        "sourceId": f"memory:{memory.id}",
                        "content": memory.content,
                        "concepts": memory.concepts,
                        "project": None,
                    },
                )
        for knowledge in self.list_knowledge():
            if not knowledge.deleted and (project is None or knowledge.project in (None, project)):
                items.append(
                    {
                        "sourceId": f"knowledge:{knowledge.id}",
                        "content": knowledge.content,
                        "concepts": knowledge.concepts or [knowledge.kind],
                        "project": knowledge.project,
                    },
                )
        return items[:limit]

    def _project_profile_evidence(self, project_id: str, limit: int) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for observation in self.list_observations():
            if observation.projectId == project_id:
                items.append({"sourceId": f"observation:{observation.id}", **observation.model_dump()})
        for summary in self.list_summaries():
            if summary.projectId == project_id:
                items.append({"sourceId": f"summary:{summary.id}", **summary.model_dump()})
        for memory in self.list_memories():
            if memory.projectId == project_id:
                items.append({"sourceId": f"memory:{memory.id}", **memory.model_dump()})
        for knowledge in self.list_knowledge():
            if knowledge.projectId == project_id and not knowledge.deleted:
                items.append({"sourceId": f"knowledge:{knowledge.id}", **knowledge.model_dump()})
        for page in self.list_wiki_pages():
            if page.projectId == project_id:
                items.append({"sourceId": f"wikiPage:{page.id}", **page.model_dump()})
        return sorted(items, key=lambda item: str(item.get("updatedAt") or item.get("createdAt") or ""), reverse=True)[:limit]

    def _group_sources_by_concepts(self, items: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
        groups: dict[str, list[dict[str, object]]] = {}
        for item in items:
            concepts = item.get("concepts")
            keys = [str(value).casefold() for value in concepts] if isinstance(concepts, list) and concepts else []
            if not keys:
                keys = _query_terms(str(item.get("content", "")))[:3]
            for key in keys:
                if len(key) < 3:
                    continue
                groups.setdefault(key, []).append(item)
        return groups

    def _consolidated_content(self, concept: str, items: list[dict[str, object]]) -> str:
        snippets = []
        for item in items[:5]:
            content = re.sub(r"\s+", " ", str(item.get("content", ""))).strip()
            snippets.append(content[:160])
        return f"{concept}: " + " / ".join(snippets)

    def _uncovered_wiki_source_ids(self, source_ids: list[str]) -> list[str]:
        covered = {source_id for item in self.list_knowledge() for source_id in item.sourceIds}
        missing = [source_id for source_id in source_ids if source_id not in covered]
        return missing or source_ids

    def _apply_wiki_proposal(
        self,
        job: WikiUpdateJobRecord,
        proposal: dict[str, object],
        existing: WikiPageRecord | None,
    ) -> WikiPageRecord:
        now = utc_now_iso()
        topic = proposal["topic"]  # type: ignore[assignment]
        source_ids = _dedupe_strings([*(existing.sourceIds if existing else []), *job.sourceIds])
        page = WikiPageRecord(
            id=existing.id if existing else generate_id("wiki"),
            title=str(proposal["title"]),
            topic=topic,  # type: ignore[arg-type]
            content=str(proposal["content"]),
            sourceIds=source_ids,
            confidence=proposal.get("confidence") if isinstance(proposal.get("confidence"), float) else None,
            scope=job.scope,
            project=job.project,
            projectId=job.projectId,
            createdAt=existing.createdAt if existing else now,
            updatedAt=now,
        )
        self.kv.set(KV.wiki_pages, page.id, page.model_dump())
        if self.search_service:
            self.search_service.index_document(wiki_page_document(page))
        self._record_audit(
            AuditRecord(
                id=generate_id("aud"),
                action="wiki_update",
                targetType="wiki_page",
                targetId=page.id,
                source="llm",
                timestamp=now,
                details={"jobId": job.id, "topic": page.topic, "sourceIds": job.sourceIds},
            ),
        )
        return page

    def _wiki_page_by_topic(
        self,
        topic: WikiTopic,
        scope: MemoryScope | None = None,
        project_id: str | None = None,
    ) -> WikiPageRecord | None:
        for page in self.list_wiki_pages():
            if page.topic == topic and page.type == "topic" and (scope is None or page.scope == scope) and (project_id is None or page.projectId == project_id):
                return page
        return None

    def _infer_wiki_topic(self, source_ids: list[str]) -> WikiTopic:
        evidence = " ".join(item.get("content", "") for item in self._wiki_evidence(source_ids)).lower()
        if any(term in evidence for term in ["preference", "偏好", "习惯"]):
            return "personal_preferences"
        if any(term in evidence for term in ["error", "failed", "fix", "修复", "报错"]):
            return "troubleshooting"
        if any(term in evidence for term in ["file", "module", "src/", ".py", "文件", "模块"]):
            return "files_and_modules"
        if any(term in evidence for term in ["workflow", "流程", "验收", "测试"]):
            return "workflow_habits"
        if any(term in evidence for term in ["decision", "决定", "选择", "技术"]):
            return "technical_decisions"
        return "project_overview"

    def _wiki_evidence(self, source_ids: list[str]) -> list[dict[str, object]]:
        evidence: list[dict[str, object]] = []
        for source_id in source_ids:
            source_type, _, entity_id = source_id.partition(":")
            item = None
            if source_type == "observation":
                for observation in self.list_observations():
                    if observation.id == entity_id:
                        item = observation.model_dump()
                        break
            elif source_type == "memory":
                item = self.kv.get(KV.memories, entity_id)
            elif source_type == "summary":
                item = self.kv.get(KV.summaries, entity_id)
            if item:
                evidence.append({"sourceId": source_id, **item})
        return evidence


def _dedupe_strings(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _governance_schema_version(payload: dict[str, object]) -> int:
    raw = payload.get("schemaVersion")
    if raw is None and payload.get("version"):
        return 1
    try:
        schema_version = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("unsupported or missing governance schemaVersion") from exc
    if schema_version > GOVERNANCE_SCHEMA_VERSION:
        raise ValueError(f"unsupported governance schemaVersion: {schema_version}")
    return schema_version


def _parse_project_profile_text(text: str) -> dict[str, object]:
    data = _json_object(text)
    if data:
        return {
            "content": str(data.get("content") or ""),
            "goals": _string_list_value(data.get("goals")),
            "techStack": _string_list_value(data.get("techStack")),
            "keyFiles": _string_list_value(data.get("keyFiles")),
            "commands": _string_list_value(data.get("commands")),
            "conventions": _string_list_value(data.get("conventions")),
            "risks": _string_list_value(data.get("risks")),
            "confidence": _float_value(data.get("confidence")),
        }
    return {
        "content": text.strip(),
        "goals": [],
        "techStack": [],
        "keyFiles": [],
        "commands": [],
        "conventions": [],
        "risks": [],
        "confidence": None,
    }


def _json_object(text: str) -> dict[str, object] | None:
    try:
        import json

        value = json.loads(text)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _string_list_value(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _float_value(value: object) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _is_list(value: object, label: str, errors: list[str]) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return True
    errors.append(f"{label}: expected list")
    return False


def _increment(counter: dict[str, int], label: str) -> None:
    counter[label] = counter.get(label, 0) + 1


def _normalize_knowledge_content(content: str) -> str:
    normalized = re.sub(r"\s+", " ", content.casefold()).strip()
    normalized = re.sub(r"[^\w\s:/.-]+", "", normalized)
    return normalized


def _knowledge_fingerprint(kind: str, content: str, source_group: str | None = None) -> str:
    parts = [kind, _normalize_knowledge_content(content)]
    if source_group:
        parts.append(source_group)
    payload = "\n".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _knowledge_source_group(source_ids: list[str]) -> str:
    normalized = "|".join(sorted(source_ids))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _select_distilled_knowledge(proposals: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates = [proposal for proposal in proposals if proposal.get("kind") in {"semantic", "procedural", "lesson"}]
    if not candidates:
        return []
    priority = {"lesson": 3, "procedural": 2, "semantic": 1}
    ranked = sorted(
        candidates,
        key=lambda item: (
            item.get("confidence") if isinstance(item.get("confidence"), float) else 0.0,
            priority.get(str(item.get("kind")), 0),
            len(str(item.get("content") or "")),
        ),
        reverse=True,
    )
    selected: list[dict[str, object]] = []
    selected_terms: list[set[str]] = []
    for candidate in ranked:
        content = str(candidate.get("content") or "")
        terms = set(_query_terms(_normalize_knowledge_content(content)))
        if not terms:
            continue
        if any(_jaccard_similarity(terms, existing) >= 0.72 for existing in selected_terms):
            continue
        selected.append(candidate)
        selected_terms.append(terms)
        if len(selected) >= 3:
            break
    return selected


def _should_distill_wiki_job(job: WikiUpdateJobRecord) -> bool:
    # Summaries are derived from observations. Let them update Wiki prose, but
    # avoid creating a second near-duplicate knowledge record for the same fact.
    return any(not source_id.startswith("summary:") for source_id in job.sourceIds)


def _unique_knowledge_records(records: list[KnowledgeRecord]) -> list[KnowledgeRecord]:
    by_id: dict[str, KnowledgeRecord] = {}
    for record in records:
        by_id[record.id] = record
    return list(by_id.values())


def _query_terms(query: str) -> list[str]:
    return [term for term in re.split(r"[\s,，。:：/\\|]+", query.casefold()) if len(term) > 1]


def _term_overlap(text: str, terms: list[str]) -> int:
    haystack = text.casefold()
    return sum(1 for term in terms if term in haystack)


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _days_between(start: str, end: str) -> int:
    try:
        from datetime import datetime

        lhs = datetime.fromisoformat(start.replace("Z", "+00:00"))
        rhs = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return max(0, int((rhs - lhs).total_seconds() // 86400))
    except Exception:
        return 0


def _crystal_content(evidence: list[dict[str, object]], source_ids: list[str]) -> str:
    snippets = [re.sub(r"\s+", " ", str(item.get("content", ""))).strip()[:180] for item in evidence[:5]]
    if snippets:
        return "Crystal digest: " + " / ".join(snippets)
    return f"Crystal digest for sources: {', '.join(source_ids)}"


def _concepts_from_evidence(evidence: list[dict[str, object]]) -> list[str]:
    concepts: list[str] = []
    for item in evidence:
        raw = item.get("concepts")
        if isinstance(raw, list):
            concepts.extend(str(value) for value in raw)
    return _dedupe_strings(concepts)


def _contains_contradiction_marker(content: str) -> bool:
    lowered = content.casefold()
    return any(term in lowered for term in ["contradict", "conflict", "supersede", "矛盾", "冲突", "取代"])
