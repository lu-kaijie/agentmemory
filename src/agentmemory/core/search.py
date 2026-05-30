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
    ContextRequest,
    ContextResponse,
    IndexJobRecord,
    IndexStatus,
    KnowledgeRecord,
    MemoryRecord,
    ObservationRecord,
    SearchDocument,
    SearchMode,
    SearchMatchMode,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SmartSearchRequest,
    SmartSearchResponse,
    SummaryRecord,
    WikiPageRecord,
)


DEFAULT_CONTEXT_SOURCE_TYPES = ["knowledge", "wikiPage", "memory", "summary"]
CONTEXT_SOURCE_PRIORITY = {"knowledge": 0, "wikiPage": 1, "memory": 2, "summary": 3, "observation": 4}
GENERIC_QUERY_TERMS = {
    "agentmemory",
    "evidence",
    "governance",
    "knowledge",
    "memory",
    "rag",
    "search",
    "wiki",
    "上下文",
    "治理",
    "搜索",
    "检索",
    "记忆",
}
DEFAULT_KEYWORD_MIN_SCORE = 0.55
DEFAULT_VECTOR_MIN_SCORE = 0.2
DEFAULT_HYBRID_MIN_SCORE = 0.3
QUESTION_OR_STOP_TERMS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "how",
    "is",
    "of",
    "or",
    "should",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
}


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
    session_id = summary.sessionId or (observation.sessionId if observation else None)
    return SearchDocument(
        id=f"doc_summary_{summary.id}",
        sourceType="summary",
        sourceId=summary.id,
        sessionId=session_id,
        content=f"{summary.kind}\n\n{summary.content}",
        searchableText=_searchable_text(summary.content, observation.files if observation else [], observation.concepts if observation else []),
        language=summary.language,
        project=observation.project if observation else None,
        files=observation.files if observation else [],
        concepts=observation.concepts if observation else [],
        createdAt=summary.createdAt,
    )


def wiki_page_document(page: WikiPageRecord) -> SearchDocument:
    return SearchDocument(
        id=f"doc_wikiPage_{page.id}",
        sourceType="wikiPage",
        sourceId=page.id,
        content=f"{page.title}\n\n{page.content}",
        searchableText=_searchable_text(
            f"{page.title}\n{page.topic}\n{page.content}\n{' '.join(page.sourceIds)}",
            [],
            [page.topic],
        ),
        language="mixed",
        files=[],
        concepts=[page.topic],
        createdAt=page.updatedAt,
    )


def knowledge_document(record: KnowledgeRecord) -> SearchDocument:
    return SearchDocument(
        id=f"doc_knowledge_{record.id}",
        sourceType="knowledge",
        sourceId=record.id,
        content=f"{record.kind}\n\n{record.content}",
        searchableText=_searchable_text(
            f"{record.kind}\n{record.content}\n{' '.join(record.sourceIds)}",
            record.files,
            [record.kind, *record.concepts],
        ),
        language="mixed",
        files=record.files,
        concepts=[record.kind, *record.concepts],
        createdAt=record.updatedAt,
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

    def delete_document(self, source_type: str, source_id: str) -> bool:
        document_id = f"doc_{source_type}_{source_id}"
        if self._vector_table_exists():
            try:
                self._table().delete(f"document_id = '{document_id}'")
            except Exception as exc:
                raise RuntimeError(f"failed to delete vector document {document_id}: {exc}") from exc
        existed = self.kv.delete(KV.search_documents, document_id)
        self.kv.fts_delete(document_id)
        for raw in self.kv.list(KV.index_jobs):
            job = IndexJobRecord.model_validate(raw)
            if job.targetType == source_type and job.targetId == source_id:
                self.kv.delete(KV.index_jobs, job.id)
        return existed

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
            min_score=request.minScore,
            match_mode=request.matchMode,
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
            min_score=request.minScore,
            match_mode=request.matchMode,
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

    def context(self, request: ContextRequest) -> ContextResponse:
        source_types = request.sourceTypes or DEFAULT_CONTEXT_SOURCE_TYPES
        results = self._search_results(
            query=request.query,
            mode="hybrid",
            limit=request.limit,
            project=request.project,
            language=request.language,
            source_types=source_types,
            min_score=request.minScore,
            match_mode=request.matchMode,
        )
        if not results:
            return ContextResponse(
                query=request.query,
                context="",
                evidence=[],
                wikiPages=[],
                knowledge=[],
                memories=[],
                confidence=0.0,
                compressed=False,
            )

        ordered = _context_order(results)
        context = _pack_context(ordered)
        compressed = False
        if _over_budget(context, request.tokenBudget):
            if self.llm:
                context = self.llm.compress_context([item.model_dump() for item in ordered], request.tokenBudget)
                compressed = True
            else:
                context = _truncate_context(context, request.tokenBudget)

        return ContextResponse(
            query=request.query,
            context=context,
            evidence=[_context_evidence(item) for item in ordered],
            wikiPages=[item for item in ordered if item.sourceType == "wikiPage"],
            knowledge=[item for item in ordered if item.sourceType == "knowledge"],
            memories=[item for item in ordered if item.sourceType in ("memory", "summary", "observation")],
            confidence=_context_confidence(ordered, compressed),
            compressed=compressed,
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
        min_score: float | None = None,
        match_mode: SearchMatchMode = "auto",
    ) -> list[SearchResult]:
        fetch_limit = min(max(limit * 4, limit), 50)
        keyword = self._keyword_search(query, fetch_limit, match_mode) if mode in ("keyword", "hybrid") else []
        vector = self._vector_search(query, fetch_limit) if mode in ("vector", "hybrid") else []
        merged = self._merge(keyword, vector, query) if mode == "hybrid" else keyword or vector
        filtered = [
            result
            for result in merged
            if (project is None or result.project == project)
            and (language is None or result.language == language)
            and (not source_types or result.sourceType in source_types)
        ]
        gated = self._relevance_gate(filtered, query=query, mode=mode, min_score=min_score, match_mode=match_mode)
        return gated[:limit]

    def _keyword_search(self, query: str, limit: int, match_mode: SearchMatchMode = "auto") -> list[SearchResult]:
        try:
            rows = self.kv.fts_search(_fts_query(query, match_mode), limit)
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

    def _merge(self, keyword: list[SearchResult], vector: list[SearchResult], query: str = "") -> list[SearchResult]:
        merged: dict[tuple[str, str], SearchResult] = {}
        for result in [*keyword, *vector]:
            key = (result.sourceType, result.sourceId)
            existing = merged.get(key)
            if existing is None:
                merged[key] = result.model_copy()
                continue
            existing.score = max(existing.score, result.score) + min(existing.score, result.score) * 0.35
            existing.matchSources = sorted(set([*existing.matchSources, *result.matchSources]))  # type: ignore[assignment]
        query_terms = _query_terms(query)
        return sorted(
            merged.values(),
            key=lambda item: (
                "keyword" in item.matchSources and "vector" in item.matchSources,
                _metadata_overlap(item, query_terms),
                item.score,
                item.createdAt,
            ),
            reverse=True,
        )

    def _relevance_gate(
        self,
        results: list[SearchResult],
        query: str,
        mode: SearchMode,
        min_score: float | None,
        match_mode: SearchMatchMode,
    ) -> list[SearchResult]:
        threshold = min_score if min_score is not None else _default_min_score(mode, match_mode)
        query_terms = _query_terms(query)
        generic_only = bool(query_terms) and all(term in GENERIC_QUERY_TERMS for term in query_terms)
        gated: list[SearchResult] = []
        for result in results:
            effective_score = result.score
            metadata_overlap = _metadata_overlap(result, query_terms)
            if len(result.matchSources) > 1:
                effective_score += 0.12
            if metadata_overlap:
                effective_score += 0.06
            generic_keyword_only = generic_only and result.matchSources == ["keyword"] and metadata_overlap == 0
            if generic_keyword_only:
                effective_score -= 0.25
            if match_mode == "any" and min_score is not None:
                passes = effective_score >= threshold
            else:
                passes = (
                    not generic_keyword_only
                    and effective_score >= threshold
                    and self._matches_keyword_mode(result, query_terms, match_mode)
                )
            if passes:
                result.score = round(max(0.0, effective_score), 6)
                gated.append(result)
        return sorted(
            gated,
            key=lambda item: (
                len(item.matchSources),
                _metadata_overlap(item, query_terms),
                item.score,
                item.createdAt,
            ),
            reverse=True,
        )

    def _matches_keyword_mode(self, result: SearchResult, query_terms: list[str], match_mode: SearchMatchMode) -> bool:
        if "keyword" not in result.matchSources or not query_terms:
            return True
        haystack = _normalize_for_match(" ".join([result.content, " ".join(result.concepts), " ".join(result.files)]))
        if match_mode == "phrase":
            return _normalize_for_match(" ".join(query_terms)) in haystack
        if match_mode == "all" or (match_mode == "auto" and _strict_auto_query(query_terms)):
            return all(term in haystack for term in query_terms if term not in GENERIC_QUERY_TERMS) or all(term in haystack for term in query_terms)
        return True

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
            observation = observations_by_id.get(summary.observationId) if summary.observationId else None
            documents.append(summary_document(summary, observation))
        for item in self.kv.list(KV.knowledge):
            documents.append(knowledge_document(KnowledgeRecord.model_validate(item)))
        for item in self.kv.list(KV.wiki_pages):
            documents.append(wiki_page_document(WikiPageRecord.model_validate(item)))
        return documents


def _dedupe_documents(documents: Iterable[SearchDocument]) -> list[SearchDocument]:
    deduped: dict[str, SearchDocument] = {}
    for document in documents:
        deduped[document.id] = document
    return list(deduped.values())


def _context_order(results: list[SearchResult]) -> list[SearchResult]:
    return sorted(
        results,
        key=lambda item: (
            CONTEXT_SOURCE_PRIORITY.get(item.sourceType, 99),
            -item.score,
            item.createdAt,
            item.sourceId,
        ),
    )


def _pack_context(results: list[SearchResult]) -> str:
    lines = ["AgentMemory context:"]
    for item in results:
        lines.append(f"- [{item.sourceType}:{item.sourceId}] {item.content.strip()}")
    return "\n".join(lines)


def _context_evidence(result: SearchResult) -> dict[str, Any]:
    return {
        "sourceType": result.sourceType,
        "sourceId": result.sourceId,
        "documentId": result.documentId,
        "content": result.content,
        "score": result.score,
        "matchSources": result.matchSources,
    }


def _over_budget(context: str, token_budget: int) -> bool:
    return _approx_tokens(context) > token_budget


def _truncate_context(context: str, token_budget: int) -> str:
    max_chars = max(0, token_budget * 4)
    if len(context) <= max_chars:
        return context
    suffix = "\n[truncated]"
    return context[: max(0, max_chars - len(suffix))].rstrip() + suffix


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _context_confidence(results: list[SearchResult], compressed: bool) -> float:
    if not results:
        return 0.0
    best_score = max(item.score for item in results)
    source_diversity = len({item.sourceType for item in results})
    match_bonus = 0.1 if any(len(item.matchSources) > 1 for item in results) else 0.0
    compression_penalty = 0.05 if compressed else 0.0
    confidence = min(0.95, 0.25 + min(best_score, 1.0) * 0.45 + min(source_diversity, 3) * 0.08 + match_bonus)
    return round(max(0.0, confidence - compression_penalty), 3)


def _escape_fts_query(query: str) -> str:
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def _fts_query(query: str, match_mode: SearchMatchMode = "auto") -> str:
    stripped = query.strip()
    if match_mode == "phrase" or (stripped.startswith('"') and stripped.endswith('"') and len(stripped) > 1):
        return _escape_fts_query(stripped.strip('"'))
    tokens = [token for token in stripped.replace("-", " ").split() if token]
    if not tokens:
        return _escape_fts_query(query)
    if match_mode == "all" or (match_mode == "auto" and _strict_auto_query([token.lower() for token in tokens])):
        return " AND ".join(_escape_fts_query(token) for token in tokens)
    return " OR ".join(_escape_fts_query(token) for token in tokens)


def _query_terms(query: str) -> list[str]:
    return [
        token.lower()
        for token in query.replace('"', " ").replace("-", " ").split()
        if token.strip()
    ]


def _strict_auto_query(query_terms: list[str]) -> bool:
    useful_terms = [term for term in query_terms if term not in GENERIC_QUERY_TERMS and term not in QUESTION_OR_STOP_TERMS]
    has_question_or_stop = any(term in QUESTION_OR_STOP_TERMS for term in query_terms)
    return not has_question_or_stop and 2 <= len(useful_terms) <= 3 and len(query_terms) <= 4


def _default_min_score(mode: SearchMode, match_mode: SearchMatchMode) -> float:
    if match_mode == "any":
        return 0.0
    if mode == "vector":
        return DEFAULT_VECTOR_MIN_SCORE
    if mode == "hybrid":
        return DEFAULT_HYBRID_MIN_SCORE
    return DEFAULT_KEYWORD_MIN_SCORE


def _metadata_overlap(result: SearchResult, query_terms: list[str]) -> int:
    if not query_terms:
        return 0
    metadata = {item.lower() for item in [*result.concepts, *result.files, result.language]}
    return len(metadata.intersection(query_terms))


def _normalize_for_match(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").split())
