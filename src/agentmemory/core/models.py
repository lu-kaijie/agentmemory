from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Language = Literal["zh", "en", "mixed", "unknown"]
SourceType = Literal["observation", "memory", "summary"]
SearchMode = Literal["keyword", "vector", "hybrid"]


class SessionRecord(BaseModel):
    id: str
    project: str | None = None
    cwd: str | None = None
    startedAt: str
    updatedAt: str
    observationCount: int = 0


class ObservationRecord(BaseModel):
    id: str
    sessionId: str
    type: str = "work-summary"
    content: str
    source: str = "cli"
    language: Language = "unknown"
    project: str | None = None
    cwd: str | None = None
    files: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    createdAt: str


class MemoryRelation(BaseModel):
    type: Literal["duplicate", "complement", "supersedes", "contradicts", "related_to"]
    targetId: str
    confidence: float | None = None


class MemoryRecord(BaseModel):
    id: str
    type: str = "fact"
    content: str
    concepts: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    language: Language = "unknown"
    source: str = "cli"
    canonicalId: str | None = None
    duplicateOf: str | None = None
    relations: list[MemoryRelation] = Field(default_factory=list)
    createdAt: str


class SummaryRecord(BaseModel):
    id: str
    observationId: str
    content: str
    source: str = "llm"
    language: Language = "unknown"
    createdAt: str


class MemoryCandidateRecord(BaseModel):
    id: str
    observationId: str
    content: str
    type: str = "fact"
    confidence: float | None = None
    concepts: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    language: Language = "unknown"
    status: Literal["candidate"] = "candidate"
    createdAt: str


class LLMProcessingJobRecord(BaseModel):
    id: str
    observationId: str
    status: Literal["running", "done", "failed"]
    summaryId: str | None = None
    candidateIds: list[str] = Field(default_factory=list)
    lastError: str | None = None
    startedAt: str
    finishedAt: str | None = None


class AuditRecord(BaseModel):
    id: str
    action: Literal[
        "observe",
        "remember",
        "llm_processing_done",
        "llm_processing_failed",
        "index_done",
        "index_failed",
    ]
    targetType: Literal["observation", "memory", "llm_processing_job", "index_job"]
    targetId: str
    source: str
    timestamp: str
    details: dict[str, Any] = Field(default_factory=dict)


class ObserveRequest(BaseModel):
    content: str = Field(min_length=1)
    sessionId: str | None = None
    type: str = "work-summary"
    source: str = "cli"
    language: Language = "unknown"
    project: str | None = None
    cwd: str | None = None
    files: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)


class ObserveResponse(BaseModel):
    observationId: str
    sessionId: str
    observation: ObservationRecord
    processingJob: LLMProcessingJobRecord | None = None
    summary: SummaryRecord | None = None
    memoryCandidates: list[MemoryCandidateRecord] = Field(default_factory=list)


class RememberRequest(BaseModel):
    content: str = Field(min_length=1)
    type: str = "fact"
    source: str = "cli"
    language: Language = "unknown"
    concepts: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    canonicalId: str | None = None
    duplicateOf: str | None = None
    relations: list[MemoryRelation] = Field(default_factory=list)


class RememberResponse(BaseModel):
    memoryId: str
    memory: MemoryRecord


class SearchDocument(BaseModel):
    id: str
    sourceType: SourceType
    sourceId: str
    sessionId: str | None = None
    content: str
    searchableText: str
    language: Language = "unknown"
    project: str | None = None
    files: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    createdAt: str


class SearchResult(BaseModel):
    documentId: str
    sourceType: SourceType
    sourceId: str
    sessionId: str | None = None
    content: str
    score: float
    language: Language = "unknown"
    project: str | None = None
    files: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    createdAt: str
    matchSources: list[Literal["keyword", "vector"]] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: SearchMode = "keyword"
    limit: int = Field(default=10, ge=1, le=50)
    project: str | None = None
    language: Language | None = None
    sourceTypes: list[SourceType] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    results: list[SearchResult] = Field(default_factory=list)


class SmartSearchRequest(SearchRequest):
    mode: SearchMode = "hybrid"


class SmartSearchResponse(BaseModel):
    query: str
    mode: SearchMode
    answer: str
    results: list[SearchResult] = Field(default_factory=list)
    evidence: list[dict[str, str]] = Field(default_factory=list)
    context: str = ""


class IndexJobRecord(BaseModel):
    id: str
    type: Literal["embedding_update", "fts_rebuild", "index_repair"]
    targetType: SourceType
    targetId: str
    status: Literal["pending", "running", "done", "failed"]
    attempts: int = 0
    lastError: str | None = None
    startedAt: str
    finishedAt: str | None = None


class IndexStatus(BaseModel):
    documents: int
    indexJobs: int
    failedJobs: int
    fts5: dict[str, Any]
    lancedb: dict[str, Any]
    embedding: dict[str, Any]
