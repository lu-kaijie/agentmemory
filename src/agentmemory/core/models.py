from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Language = Literal["zh", "en", "mixed", "unknown"]
SourceType = Literal["observation", "memory", "summary", "wikiPage", "knowledge"]
SearchMode = Literal["keyword", "vector", "hybrid"]
SearchMatchMode = Literal["auto", "any", "all", "phrase"]
KnowledgeKind = Literal["semantic", "procedural", "lesson", "crystal"]
WikiTopic = Literal[
    "personal_preferences",
    "project_overview",
    "technical_decisions",
    "troubleshooting",
    "files_and_modules",
    "workflow_habits",
]


WIKI_TOPICS: tuple[WikiTopic, ...] = (
    "personal_preferences",
    "project_overview",
    "technical_decisions",
    "troubleshooting",
    "files_and_modules",
    "workflow_habits",
)


class SessionRecord(BaseModel):
    id: str
    project: str | None = None
    cwd: str | None = None
    startedAt: str
    updatedAt: str
    observationCount: int = 0
    status: Literal["active", "ended"] = "active"
    endedAt: str | None = None
    summaryId: str | None = None


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
    observationId: str | None = None
    sessionId: str | None = None
    kind: Literal["observation", "session"] = "observation"
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


class WikiPageRecord(BaseModel):
    id: str
    title: str
    topic: WikiTopic
    content: str
    sourceIds: list[str] = Field(default_factory=list)
    confidence: float | None = None
    createdAt: str
    updatedAt: str


class KnowledgeRecord(BaseModel):
    id: str
    kind: KnowledgeKind
    content: str
    sourceIds: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    confidence: float | None = None
    fingerprint: str | None = None
    reinforcements: int = 0
    lastReinforcedAt: str | None = None
    sourceGroup: str | None = None
    createdAt: str
    updatedAt: str


class WikiUpdateJobRecord(BaseModel):
    id: str
    sourceIds: list[str] = Field(default_factory=list)
    topic: WikiTopic | None = None
    status: Literal["pending", "running", "applied", "failed"]
    proposal: dict[str, Any] | None = None
    attempts: int = 0
    lastError: str | None = None
    createdAt: str
    updatedAt: str


class AuditRecord(BaseModel):
    id: str
    action: Literal[
        "observe",
        "remember",
        "export",
        "forget",
        "llm_processing_done",
        "llm_processing_failed",
        "index_done",
        "index_failed",
        "knowledge_distill",
        "session_end",
        "session_start",
        "wiki_update",
    ]
    targetType: Literal[
        "observation",
        "memory",
        "session",
        "llm_processing_job",
        "index_job",
        "governance",
        "knowledge",
        "wiki_page",
    ]
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


class SessionStartRequest(BaseModel):
    sessionId: str | None = None
    source: str = "cli"
    project: str | None = None
    cwd: str | None = None


class SessionStartResponse(BaseModel):
    sessionId: str
    session: SessionRecord


class SessionEndRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    source: str = "cli"
    content: str | None = None
    language: Language = "unknown"
    project: str | None = None
    cwd: str | None = None


class SessionEndResponse(BaseModel):
    sessionId: str
    session: SessionRecord
    summary: SummaryRecord | None = None
    error: str | None = None


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


class ForgetRequest(BaseModel):
    memoryId: str = Field(min_length=1)
    source: str = "cli"
    reason: str | None = None


class ForgetResponse(BaseModel):
    memoryId: str
    auditId: str
    deletedMemory: MemoryRecord


class GovernanceExport(BaseModel):
    version: str
    exportedAt: str
    sessions: list[SessionRecord] = Field(default_factory=list)
    observations: list[ObservationRecord] = Field(default_factory=list)
    memories: list[MemoryRecord] = Field(default_factory=list)
    summaries: list[SummaryRecord] = Field(default_factory=list)
    memoryCandidates: list[MemoryCandidateRecord] = Field(default_factory=list)
    llmProcessingJobs: list[LLMProcessingJobRecord] = Field(default_factory=list)
    knowledge: list[KnowledgeRecord] = Field(default_factory=list)
    wikiPages: list[WikiPageRecord] = Field(default_factory=list)
    wikiUpdateJobs: list[WikiUpdateJobRecord] = Field(default_factory=list)
    indexJobs: list["IndexJobRecord"] = Field(default_factory=list)
    audit: list[AuditRecord] = Field(default_factory=list)


class WikiUpdateRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)


class WikiRebuildRequest(BaseModel):
    topic: WikiTopic | None = None
    all: bool = False


class WikiUpdateResponse(BaseModel):
    jobs: list[WikiUpdateJobRecord] = Field(default_factory=list)
    pages: list[WikiPageRecord] = Field(default_factory=list)
    knowledge: list[KnowledgeRecord] = Field(default_factory=list)


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
    minScore: float | None = Field(default=None, ge=0.0)
    matchMode: SearchMatchMode = "auto"


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


class ContextRequest(BaseModel):
    query: str = Field(min_length=1)
    tokenBudget: int = Field(default=1200, ge=100, le=20000)
    limit: int = Field(default=10, ge=1, le=50)
    project: str | None = None
    language: Language | None = None
    sourceTypes: list[SourceType] = Field(default_factory=list)
    minScore: float | None = Field(default=None, ge=0.0)
    matchMode: SearchMatchMode = "auto"


class ContextResponse(BaseModel):
    query: str
    context: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    wikiPages: list[SearchResult] = Field(default_factory=list)
    knowledge: list[SearchResult] = Field(default_factory=list)
    memories: list[SearchResult] = Field(default_factory=list)
    confidence: float = 0.0
    compressed: bool = False


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
