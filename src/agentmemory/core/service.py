from __future__ import annotations

import asyncio
import hashlib
import re

from agentmemory.core.ids import generate_id, utc_now_iso
from agentmemory.core.models import (
    AuditRecord,
    ContextRequest,
    ForgetRequest,
    ForgetResponse,
    GovernanceExport,
    IndexJobRecord,
    KnowledgeRecord,
    LLMProcessingJobRecord,
    MemoryCandidateRecord,
    MemoryRecord,
    ObserveRequest,
    ObserveResponse,
    ObservationRecord,
    RememberRequest,
    RememberResponse,
    SessionEndRequest,
    SessionEndResponse,
    SessionRecord,
    SessionStartRequest,
    SessionStartResponse,
    SummaryRecord,
    WIKI_TOPICS,
    WikiPageRecord,
    WikiRebuildRequest,
    WikiTopic,
    WikiUpdateJobRecord,
    WikiUpdateRequest,
    WikiUpdateResponse,
)
from agentmemory.core.processing import create_running_job, process_observation
from agentmemory.core.search import MemorySearchService, knowledge_document, memory_document, observation_document, summary_document, wiki_page_document
from agentmemory.core.wiki import WIKI_TITLES, parse_knowledge_xml, parse_wiki_update_xml
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
            session.status = "active"
            session.endedAt = None
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
                self._enqueue_wiki_job([f"summary:{summary.id}"])
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

    def start_session(self, request: SessionStartRequest) -> SessionStartResponse:
        now = utc_now_iso()
        session_id = request.sessionId or generate_id("ses")
        existing = self.kv.get(KV.sessions, session_id)
        if existing:
            session = SessionRecord.model_validate(existing)
            session.project = request.project or session.project
            session.cwd = request.cwd or session.cwd
            session.updatedAt = now
            session.status = "active"
            session.endedAt = None
        else:
            session = SessionRecord(
                id=session_id,
                project=request.project,
                cwd=request.cwd,
                startedAt=now,
                updatedAt=now,
                observationCount=0,
            )
        self.kv.set(KV.sessions, session.id, session.model_dump())
        self._record_audit(
            AuditRecord(
                id=generate_id("aud"),
                action="session_start",
                targetType="session",
                targetId=session.id,
                source=request.source,
                timestamp=now,
                details={"project": session.project, "cwd": session.cwd},
            ),
        )
        return SessionStartResponse(sessionId=session.id, session=session)

    def end_session(self, request: SessionEndRequest) -> SessionEndResponse:
        now = utc_now_iso()
        raw = self.kv.get(KV.sessions, request.sessionId)
        session = (
            SessionRecord.model_validate(raw)
            if raw
            else SessionRecord(
                id=request.sessionId,
                project=request.project,
                cwd=request.cwd,
                startedAt=now,
                updatedAt=now,
                observationCount=0,
            )
        )
        session.project = request.project or session.project
        session.cwd = request.cwd or session.cwd
        session.status = "ended"
        session.endedAt = now
        session.updatedAt = now

        summary = None
        error = None
        observations = [
            ObservationRecord.model_validate(item)
            for item in self.kv.list(KV.observations(session.id))
        ]
        if self.llm and observations:
            try:
                summary_text = self.llm.summarize(
                    _session_summary_input(session, observations, request.content),
                    "Summarize this coding-agent session into one concise session memory summary.",
                )
                summary = SummaryRecord(
                    id=generate_id("sum"),
                    observationId=None,
                    sessionId=session.id,
                    kind="session",
                    content=summary_text,
                    language=request.language,
                    createdAt=now,
                )
                self.kv.set(KV.summaries, summary.id, summary.model_dump())
                session.summaryId = summary.id
                self._enqueue_wiki_job([f"summary:{summary.id}"])
                if self.search_service:
                    self.search_service.index_document(summary_document(summary))
            except Exception as exc:
                error = str(exc)

        self.kv.set(KV.sessions, session.id, session.model_dump())
        self._record_audit(
            AuditRecord(
                id=generate_id("aud"),
                action="session_end",
                targetType="session",
                targetId=session.id,
                source=request.source,
                timestamp=now,
                details={
                    "summaryId": summary.id if summary else None,
                    "observationCount": len(observations),
                    "lastError": error,
                },
            ),
        )
        return SessionEndResponse(sessionId=session.id, session=session, summary=summary, error=error)

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

    def list_wiki_pages(self) -> list[WikiPageRecord]:
        items = [WikiPageRecord.model_validate(item) for item in self.kv.list(KV.wiki_pages)]
        return sorted(items, key=lambda item: item.updatedAt)

    def list_knowledge(self) -> list[KnowledgeRecord]:
        items = [KnowledgeRecord.model_validate(item) for item in self.kv.list(KV.knowledge)]
        return sorted(items, key=lambda item: item.updatedAt)

    def list_wiki_jobs(self) -> list[WikiUpdateJobRecord]:
        items = [WikiUpdateJobRecord.model_validate(item) for item in self.kv.list(KV.wiki_update_jobs)]
        return sorted(items, key=lambda item: item.createdAt)

    def process_wiki_updates(self, request: WikiUpdateRequest | None = None) -> WikiUpdateResponse:
        if not self.llm:
            raise RuntimeError("llm provider is not configured")
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
            processed, page, distilled = self._process_wiki_job(job)
            jobs.append(processed)
            if page:
                pages.append(page)
            knowledge.extend(distilled)
        return WikiUpdateResponse(jobs=jobs, pages=pages, knowledge=knowledge)

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
        jobs = [self._enqueue_wiki_job(source_ids, topic=topic) for topic in topics]
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
        return WikiUpdateResponse(jobs=processed, pages=pages, knowledge=knowledge)

    async def run_wiki_worker(self, stop_event: asyncio.Event, interval_seconds: float = 10.0) -> None:
        while not stop_event.is_set():
            await asyncio.to_thread(self.process_wiki_updates, WikiUpdateRequest(limit=5))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                pass

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
        knowledge = self.list_knowledge()
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
                "knowledge": len(knowledge),
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
            knowledge=knowledge,
            wikiPages=self.list_wiki_pages(),
            wikiUpdateJobs=self.list_wiki_jobs(),
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

    def _record_audit(self, record: AuditRecord) -> None:
        self.kv.set(KV.audit, record.id, record.model_dump())

    def _enqueue_wiki_job(
        self,
        source_ids: list[str],
        topic: WikiTopic | None = None,
    ) -> WikiUpdateJobRecord:
        now = utc_now_iso()
        job = WikiUpdateJobRecord(
            id=generate_id("wiki_job"),
            sourceIds=_dedupe_strings(source_ids),
            topic=topic,
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
            existing = self._wiki_page_by_topic(topic)
            title = existing.title if existing else WIKI_TITLES[topic]
            evidence = self._wiki_evidence(job.sourceIds)
            distilled = self._distill_knowledge(job, evidence)
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
        proposals = parse_knowledge_xml(raw)
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
        if existing.kind == "lesson":
            existing.reinforcements += 1
            existing.lastReinforcedAt = now
            if existing.confidence is not None:
                existing.confidence = min(0.99, round(existing.confidence + 0.03, 3))
        self.kv.set(KV.knowledge, existing.id, existing.model_dump())
        if self.search_service:
            self.search_service.index_document(knowledge_document(existing))
        return existing

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

    def _wiki_page_by_topic(self, topic: WikiTopic) -> WikiPageRecord | None:
        for page in self.list_wiki_pages():
            if page.topic == topic:
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


def _session_summary_input(
    session: SessionRecord,
    observations: list[ObservationRecord],
    closing_note: str | None = None,
) -> str:
    lines = [
        f"Session: {session.id}",
        f"Project: {session.project or ''}",
        f"CWD: {session.cwd or ''}",
    ]
    if closing_note:
        lines.extend(["Closing note:", closing_note.strip()])
    lines.append("Observations:")
    for observation in sorted(observations, key=lambda item: item.createdAt):
        lines.append(f"- [{observation.type}] {observation.content}")
    return "\n".join(lines)


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
