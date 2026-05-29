from __future__ import annotations

import asyncio
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import lancedb

from agentmemory.config import Settings
from agentmemory.providers import EmbeddingProvider, LLMProvider
from agentmemory.state import StateKV
from agentmemory.state.schema import KV

from .ids import generate_id, utc_now_iso
from .models import (
    IndexJobRecord,
    IndexStatus,
    MemoryRecord,
    ObservationRecord,
    SearchDocument,
    SearchMode,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SmartSearchRequest,
    SmartSearchResponse,
    SummaryRecord,
)


def observation_document(observation: ObservationRecord) -> SearchDocument:
    return SearchDocument(
        id=f"doc_observation_{observation.id}",
        sourceType="observation",
        sourceId=observation.id,
        sessionId=observation.sessionId,
        content=observation.content,
        searchableText=_searchable_text(observation.content, observation.files, observation.concepts),
        language=observation.language,
        project=observation.project,
        files=observation.files,
        concepts=observation.concepts,
        createdAt=observation.createdAt,
    )


def memory_document(memory: MemoryRecord) -> SearchDocument:
    return SearchDocument(
        id=f"doc_memory_{memory.id}",
        sourceType="memory",
        sourceId=memory.id,
        content=memory.content,
        searchableText=_searchable_text(memory.content, memory.files, memory.concepts),
        language=memory.language,
        files=memory.files,
        concepts=memory.concepts,
        createdAt=memory.createdAt,
    )


def summary_document(summary: SummaryRecord, observation: ObservationRecord | None = None) -> SearchDocument:
    return SearchDocument(
        id=f"doc_summary_{summary.id}",
        sourceType="summary",
        sourceId=summary.id,
        sessionId=observation.sessionId if observation else None,
        content=summary.content,
        searchableText=_searchable_text(summary.content, observation.files if observation else [], observation.concepts if observation else []),
        language=summary.language,
        project=observation.project if observation else None,
        files=observation.files if observation else [],
        concepts=observation.concepts if observation else [],
        createdAt=summary.createdAt,
    )


def _searchable_text(content: str, files: list[str], concepts: list[str]) -> str:
    pieces = [content, " ".join(files), " ".join(concepts)]
    pieces.extend(_cjk_bigrams(content))
    return "\n".join(piece for piece in pieces if piece)


def _cjk_bigrams(text: str) -> list[str]:
    chars = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    return ["".join(chars[index : index + 2]) for index in range(max(0, len(chars) - 1))]


class MemorySearchService:
    def __init__(
        self,
        kv: StateKV,
        settings: Settings,
        embedding: EmbeddingProvider,
        llm: LLMProvider | None = None,
    ):
        self.kv = kv
        self.settings = settings
        self.embedding = embedding
        self.llm = llm
        self.vector_path = Path(settings.vector_db_path).expanduser()
        self.vector_table = settings.vector_table

    def index_document(self, document: SearchDocument) -> IndexJobRecord:
        self.kv.set(KV.search_documents, document.id, document.model_dump())
        self.kv.fts_upsert(document.model_dump())
        job = self._pending_job(document)
        self.kv.set(KV.index_jobs, job.id, job.model_dump())
        return job

    async def run_pending_worker(self, stop_event: asyncio.Event, interval_seconds: float = 1.0) -> None:
        while not stop_event.is_set():
            await asyncio.to_thread(self.process_pending, 25)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                pass

    def process_pending(self, limit: int = 25) -> list[IndexJobRecord]:
        jobs = [
            IndexJobRecord.model_validate(item)
            for item in self.kv.list(KV.index_jobs)
            if item.get("status") == "pending"
        ]
        jobs = sorted(jobs, key=lambda item: item.startedAt)[:limit]
        return [self._process_job(job) for job in jobs]

    def _process_job(self, job: IndexJobRecord) -> IndexJobRecord:
        raw = self.kv.get(KV.search_documents, f"doc_{job.targetType}_{job.targetId}")
        if not raw:
            job.status = "failed"
            job.lastError = "search document not found"
            job.finishedAt = utc_now_iso()
            self.kv.set(KV.index_jobs, job.id, job.model_dump())
            return job
        document = SearchDocument.model_validate(raw)
        job.status = "running"
        job.attempts += 1
        job.startedAt = utc_now_iso()
        job.finishedAt = None
        job.lastError = None
        self.kv.set(KV.index_jobs, job.id, job.model_dump())
        try:
            vector = self.embedding.embed_texts([document.searchableText])[0]
            self._vector_upsert(document, vector)
            job.status = "done"
            job.finishedAt = utc_now_iso()
            self.kv.set(KV.index_jobs, job.id, job.model_dump())
            return job
        except Exception as exc:
            job.status = "failed"
            job.lastError = str(exc)
            job.finishedAt = utc_now_iso()
            self.kv.set(KV.index_jobs, job.id, job.model_dump())
            return job

    def search(self, request: SearchRequest) -> SearchResponse:
        results = self._search_results(
            query=request.query,
            mode=request.mode,
            limit=request.limit,
            project=request.project,
            language=request.language,
            source_types=request.sourceTypes,
        )
        return SearchResponse(query=request.query, mode=request.mode, results=results)

    def smart_search(self, request: SmartSearchRequest) -> SmartSearchResponse:
        results = self._search_results(
            query=request.query,
            mode=request.mode,
            limit=request.limit,
            project=request.project,
            language=request.language,
            source_types=request.sourceTypes,
        )
        evidence = [
            {"sourceType": item.sourceType, "sourceId": item.sourceId, "documentId": item.documentId}
            for item in results
        ]
        if not results:
            return SmartSearchResponse(
                query=request.query,
                mode=request.mode,
                answer="未找到相关记忆。",
                results=[],
                evidence=[],
                context="",
            )
        result_dicts = [item.model_dump() for item in results]
        answer = self.llm.explain_search(request.query, result_dicts) if self.llm else "找到相关记忆。"
        context = "\n\n".join(f"[{item.sourceType}:{item.sourceId}] {item.content}" for item in results)
        return SmartSearchResponse(
            query=request.query,
            mode=request.mode,
            answer=answer,
            results=results,
            evidence=evidence,
            context=context,
        )

    def status(self) -> IndexStatus:
        jobs = [IndexJobRecord.model_validate(item) for item in self.kv.list(KV.index_jobs)]
        latest_jobs = self._latest_jobs(jobs)
        vector_ok = True
        vector_error = None
        try:
            self._vector_table_exists()
        except Exception as exc:
            vector_ok = False
            vector_error = str(exc)
        embedding_status = self.embedding.status().model_dump()
        return IndexStatus(
            documents=len(self.kv.list(KV.search_documents)),
            indexJobs=len(jobs),
            failedJobs=len([job for job in latest_jobs.values() if job.status == "failed"]),
            fts5={"ok": True, "documents": self.kv.fts_count()},
            lancedb={
                "ok": vector_ok,
                "path": str(self.vector_path),
                "table": self.vector_table,
                "exists": self._vector_table_exists() if vector_ok else False,
                "error": vector_error,
            },
            embedding=embedding_status,
        )

    def rebuild(self) -> dict[str, Any]:
        self.kv.fts_delete_all()
        self._drop_vector_table()
        documents = self._source_documents()
        jobs = [self._process_job(self.index_document(document)) for document in documents]
        return {"documents": len(documents), "jobs": [job.model_dump() for job in jobs]}

    def repair(self) -> dict[str, Any]:
        documents = [SearchDocument.model_validate(item) for item in self.kv.list(KV.search_documents)]
        indexed_ids = {document.id for document in documents}
        source_documents = self._source_documents()
        missing = [document for document in source_documents if document.id not in indexed_ids]
        latest_jobs = self._latest_jobs(
            [IndexJobRecord.model_validate(item) for item in self.kv.list(KV.index_jobs)],
        )
        failed_or_pending_jobs = [
            job
            for job in latest_jobs.values()
            if job.status in ("failed", "pending")
        ]
        failed_targets = {
            (job.targetType, job.targetId)
            for job in failed_or_pending_jobs
        }
        retry = [
            document
            for document in documents
            if (document.sourceType, document.sourceId) in failed_targets
        ]
        to_index = _dedupe_documents([*missing, *retry])
        jobs_by_target = {(job.targetType, job.targetId): job for job in failed_or_pending_jobs}
        jobs = []
        for document in to_index:
            job = jobs_by_target.get((document.sourceType, document.sourceId))
            if job is None:
                job = self.index_document(document)
            jobs.append(self._process_job(job))
        return {"documents": len(to_index), "jobs": [job.model_dump() for job in jobs]}

    def _search_results(
        self,
        query: str,
        mode: SearchMode,
        limit: int,
        project: str | None,
        language: str | None,
        source_types: list[str],
    ) -> list[SearchResult]:
        keyword = self._keyword_search(query, limit) if mode in ("keyword", "hybrid") else []
        vector = self._vector_search(query, limit) if mode in ("vector", "hybrid") else []
        merged = self._merge(keyword, vector) if mode == "hybrid" else keyword or vector
        filtered = [
            result
            for result in merged
            if (project is None or result.project == project)
            and (language is None or result.language == language)
            and (not source_types or result.sourceType in source_types)
        ]
        return filtered[:limit]

    def _keyword_search(self, query: str, limit: int) -> list[SearchResult]:
        try:
            rows = self.kv.fts_search(_fts_query(query), limit)
        except Exception:
            rows = self.kv.fts_search(_escape_fts_query(query), limit)
        return [
            SearchResult(
                documentId=row["documentId"],
                sourceType=row["sourceType"],
                sourceId=row["sourceId"],
                sessionId=row["sessionId"],
                content=row["content"],
                score=float(row["score"]),
                language=row["language"],
                project=row["project"],
                files=row["files"],
                concepts=row["concepts"],
                createdAt=row["createdAt"],
                matchSources=["keyword"],
            )
            for row in rows
        ]

    def _vector_search(self, query: str, limit: int) -> list[SearchResult]:
        if not self._vector_table_exists():
            return []
        vector = self.embedding.embed_texts([query])[0]
        if self._vector_dimension() not in (None, len(vector)):
            self.rebuild()
        try:
            rows = self._table().search(vector, vector_column_name="vector").limit(limit).to_list()
        except Exception:
            return []
        results: list[SearchResult] = []
        for row in rows:
            document_id = str(row["document_id"])
            document = self.kv.get(KV.search_documents, document_id)
            if not document:
                continue
            parsed = SearchDocument.model_validate(document)
            distance = float(row.get("_distance") or 0.0)
            results.append(
                SearchResult(
                    documentId=parsed.id,
                    sourceType=parsed.sourceType,
                    sourceId=parsed.sourceId,
                    sessionId=parsed.sessionId,
                    content=parsed.content,
                    score=1.0 / (1.0 + distance),
                    language=parsed.language,
                    project=parsed.project,
                    files=parsed.files,
                    concepts=parsed.concepts,
                    createdAt=parsed.createdAt,
                    matchSources=["vector"],
                ),
            )
        return results

    def _merge(self, keyword: list[SearchResult], vector: list[SearchResult]) -> list[SearchResult]:
        merged: dict[tuple[str, str], SearchResult] = {}
        for result in [*keyword, *vector]:
            key = (result.sourceType, result.sourceId)
            existing = merged.get(key)
            if existing is None:
                merged[key] = result.model_copy()
                continue
            existing.score = max(existing.score, result.score) + min(existing.score, result.score) * 0.25
            existing.matchSources = sorted(set([*existing.matchSources, *result.matchSources]))  # type: ignore[assignment]
        return sorted(
            merged.values(),
            key=lambda item: (
                "keyword" in item.matchSources and "vector" in item.matchSources,
                item.score,
            ),
            reverse=True,
        )

    def _pending_job(self, document: SearchDocument) -> IndexJobRecord:
        now = utc_now_iso()
        return IndexJobRecord(
            id=generate_id("idx"),
            type="embedding_update",
            targetType=document.sourceType,
            targetId=document.sourceId,
            status="pending",
            attempts=0,
            startedAt=now,
        )

    def _vector_upsert(self, document: SearchDocument, vector: list[float]) -> None:
        table = self._table(vector)
        try:
            table.delete(f"document_id = '{document.id}'")
        except Exception:
            pass
        table.add(
            [
                {
                    "vector": vector,
                    "document_id": document.id,
                    "source_type": document.sourceType,
                    "source_id": document.sourceId,
                    "embedding_model": self.settings.embedding_model,
                    "dimension": len(vector),
                },
            ],
        )

    def _table(self, sample_vector: list[float] | None = None):
        self.vector_path.mkdir(parents=True, exist_ok=True)
        db = lancedb.connect(self.vector_path)
        names = self._table_names(db)
        if self.vector_table in names:
            return db.open_table(self.vector_table)
        if sample_vector is None:
            raise RuntimeError("vector table does not exist")
        vector = sample_vector or [0.0, 0.0, 0.0]
        return db.create_table(
            self.vector_table,
            data=[
                {
                    "vector": vector,
                    "document_id": "__bootstrap__",
                    "source_type": "bootstrap",
                    "source_id": "__bootstrap__",
                    "embedding_model": self.settings.embedding_model,
                    "dimension": len(vector),
                },
            ],
        )

    def _vector_table_exists(self) -> bool:
        self.vector_path.mkdir(parents=True, exist_ok=True)
        db = lancedb.connect(self.vector_path)
        return self.vector_table in self._table_names(db)

    def _drop_vector_table(self) -> None:
        self.vector_path.mkdir(parents=True, exist_ok=True)
        db = lancedb.connect(self.vector_path)
        if self.vector_table in self._table_names(db):
            db.drop_table(self.vector_table)

    def _table_names(self, db) -> set[str]:
        response = db.list_tables()
        tables = getattr(response, "tables", response)
        return {str(item) for item in tables}

    def _vector_dimension(self) -> int | None:
        if not self._vector_table_exists():
            return None
        try:
            table = self._table()
            field = table.schema.field("vector")
            return int(getattr(field.type, "list_size", 0) or 0) or None
        except Exception:
            return None

    def _latest_jobs(self, jobs: list[IndexJobRecord]) -> dict[tuple[str, str], IndexJobRecord]:
        latest: dict[tuple[str, str], IndexJobRecord] = {}
        for job in sorted(jobs, key=lambda item: item.startedAt):
            latest[(job.targetType, job.targetId)] = job
        return latest

    def _source_documents(self) -> list[SearchDocument]:
        documents: list[SearchDocument] = []
        sessions = self.kv.list(KV.sessions)
        for session in sessions:
            session_id = str(session["id"])
            for item in self.kv.list(KV.observations(session_id)):
                documents.append(observation_document(ObservationRecord.model_validate(item)))
        for item in self.kv.list(KV.memories):
            documents.append(memory_document(MemoryRecord.model_validate(item)))
        observations_by_id = {
            item.id: item
            for session in sessions
            for item in [
                ObservationRecord.model_validate(raw)
                for raw in self.kv.list(KV.observations(str(session["id"])))
            ]
        }
        for item in self.kv.list(KV.summaries):
            summary = SummaryRecord.model_validate(item)
            documents.append(summary_document(summary, observations_by_id.get(summary.observationId)))
        return documents


def _dedupe_documents(documents: Iterable[SearchDocument]) -> list[SearchDocument]:
    deduped: dict[str, SearchDocument] = {}
    for document in documents:
        deduped[document.id] = document
    return list(deduped.values())


def _escape_fts_query(query: str) -> str:
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def _fts_query(query: str) -> str:
    tokens = [token for token in query.replace("-", " ").split() if token]
    if not tokens:
        return _escape_fts_query(query)
    return " OR ".join(_escape_fts_query(token) for token in tokens)
