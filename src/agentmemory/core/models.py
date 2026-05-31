from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Language = Literal["zh", "en", "mixed", "unknown"]
SourceType = Literal["observation", "memory", "summary", "wikiPage", "knowledge", "insight"]
SearchMode = Literal["keyword", "vector", "hybrid"]
SearchMatchMode = Literal["auto", "any", "all", "phrase"]
KnowledgeKind = Literal["semantic", "procedural", "lesson", "crystal"]
MemoryScope = Literal["global", "project"]
ContextSectionName = Literal[
    "identity",
    "global",
    "project",
    "wiki-synthesis",
    "lessons-and-crystals",
    "recent-evidence",
    "evidence",
]
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


class ObservationRecord(BaseModel):
    id: str
    type: str = "work-summary"
    content: str
    source: str = "cli"
    language: Language = "unknown"
    project: str | None = None
    projectId: str | None = None
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
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None
    createdAt: str


class SummaryRecord(BaseModel):
    id: str
    observationId: str | None = None
    kind: Literal["observation"] = "observation"
    content: str
    source: str = "llm"
    language: Language = "unknown"
    scope: MemoryScope = "project"
    project: str | None = None
    projectId: str | None = None
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
    status: Literal["pending", "running", "done", "failed"]
    summaryId: str | None = None
    candidateIds: list[str] = Field(default_factory=list)
    attempts: int = 0
    lastError: str | None = None
    startedAt: str
    finishedAt: str | None = None


class WikiPageRecord(BaseModel):
    id: str
    title: str
    topic: WikiTopic
    type: Literal["topic", "entity", "concept", "source", "comparison", "synthesis"] = "topic"
    slug: str | None = None
    parentTopic: WikiTopic | None = None
    content: str
    sourceIds: list[str] = Field(default_factory=list)
    confidence: float | None = None
    scope: MemoryScope = "project"
    project: str | None = None
    projectId: str | None = None
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
    decayRate: float = 0.05
    lastDecayedAt: str | None = None
    deleted: bool = False
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None
    query: str | None = None
    sourceGroup: str | None = None
    createdAt: str
    updatedAt: str


class InsightRecord(BaseModel):
    id: str
    title: str
    content: str
    sourceIds: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    confidence: float | None = None
    fingerprint: str | None = None
    reinforcements: int = 0
    lastReinforcedAt: str | None = None
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None
    query: str | None = None
    createdAt: str
    updatedAt: str


class WikiLintIssue(BaseModel):
    type: Literal["contradiction", "stale", "low_confidence", "missing_source", "orphan"]
    severity: Literal["info", "warning", "error"] = "warning"
    message: str
    sourceIds: list[str] = Field(default_factory=list)
    suggestedAction: str = ""


class WikiLintResponse(BaseModel):
    issues: list[WikiLintIssue] = Field(default_factory=list)


class WikiConsolidateRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=500)
    minEvidence: int = Field(default=2, ge=1, le=20)
    scope: MemoryScope = "project"
    project: str | None = None
    projectId: str | None = None


class WikiConsolidateResponse(BaseModel):
    semantic: list[KnowledgeRecord] = Field(default_factory=list)
    procedural: list[KnowledgeRecord] = Field(default_factory=list)
    pages: list[WikiPageRecord] = Field(default_factory=list)
    lintIssues: list[WikiLintIssue] = Field(default_factory=list)
    skipped: dict[str, Any] = Field(default_factory=dict)


class LessonRecallRequest(BaseModel):
    query: str = Field(min_length=1)
    minConfidence: float = Field(default=0.1, ge=0.0, le=1.0)
    project: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class LessonRecallResponse(BaseModel):
    lessons: list[KnowledgeRecord] = Field(default_factory=list)


class CrystalCreateRequest(BaseModel):
    sourceIds: list[str] = Field(default_factory=list, min_length=1)
    project: str | None = None


class CrystalCreateResponse(BaseModel):
    crystal: KnowledgeRecord
    lessons: list[KnowledgeRecord] = Field(default_factory=list)


class WikiReflectRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=500)
    project: str | None = None


class WikiReflectResponse(BaseModel):
    insights: list[InsightRecord] = Field(default_factory=list)
    reinforced: int = 0
    skipped: dict[str, Any] = Field(default_factory=dict)


class WikiFileAnswerRequest(BaseModel):
    query: str = Field(min_length=1)
    content: str = Field(min_length=1)
    kind: Literal["semantic", "procedural", "lesson", "crystal", "insight"] = "insight"
    sourceIds: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    project: str | None = None


class WikiFileAnswerResponse(BaseModel):
    record: KnowledgeRecord | InsightRecord


class WikiUpdateJobRecord(BaseModel):
    id: str
    sourceIds: list[str] = Field(default_factory=list)
    topic: WikiTopic | None = None
    scope: MemoryScope = "project"
    project: str | None = None
    projectId: str | None = None
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
        "import",
        "llm_processing_done",
        "llm_processing_failed",
        "index_done",
        "index_failed",
        "knowledge_distill",
        "wiki_update",
    ]
    targetType: Literal[
        "observation",
        "memory",
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
    type: str = "work-summary"
    source: str = "cli"
    language: Language = "unknown"
    project: str | None = None
    projectId: str | None = None
    cwd: str | None = None
    files: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)


class ObserveResponse(BaseModel):
    observationId: str
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
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None


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
    schemaVersion: int = 1
    exportedAt: str
    projects: list["ProjectRecord"] = Field(default_factory=list)
    projectProfiles: list["ProjectProfileRecord"] = Field(default_factory=list)
    pinnedMemory: list["PinnedMemoryRecord"] = Field(default_factory=list)
    observations: list[ObservationRecord] = Field(default_factory=list)
    memories: list[MemoryRecord] = Field(default_factory=list)
    summaries: list[SummaryRecord] = Field(default_factory=list)
    memoryCandidates: list[MemoryCandidateRecord] = Field(default_factory=list)
    llmProcessingJobs: list[LLMProcessingJobRecord] = Field(default_factory=list)
    knowledge: list[KnowledgeRecord] = Field(default_factory=list)
    insights: list[InsightRecord] = Field(default_factory=list)
    wikiPages: list[WikiPageRecord] = Field(default_factory=list)
    wikiUpdateJobs: list[WikiUpdateJobRecord] = Field(default_factory=list)
    indexJobs: list["IndexJobRecord"] = Field(default_factory=list)
    audit: list[AuditRecord] = Field(default_factory=list)


class GovernanceImportRequest(BaseModel):
    payload: dict[str, Any]
    source: str = "cli"


class GovernanceImportResponse(BaseModel):
    schemaVersion: int
    imported: dict[str, int] = Field(default_factory=dict)
    skipped: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    auditId: str


class WikiUpdateRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    scope: MemoryScope = "project"
    project: str | None = None
    projectId: str | None = None


class WikiRebuildRequest(BaseModel):
    topic: WikiTopic | None = None
    all: bool = False
    scope: MemoryScope = "project"
    project: str | None = None
    projectId: str | None = None


class WikiUpdateResponse(BaseModel):
    jobs: list[WikiUpdateJobRecord] = Field(default_factory=list)
    pages: list[WikiPageRecord] = Field(default_factory=list)
    knowledge: list[KnowledgeRecord] = Field(default_factory=list)


class SearchDocument(BaseModel):
    id: str
    sourceType: SourceType
    sourceId: str
    content: str
    searchableText: str
    language: Language = "unknown"
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None
    files: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    createdAt: str


class SearchResult(BaseModel):
    documentId: str
    sourceType: SourceType
    sourceId: str
    content: str
    score: float
    language: Language = "unknown"
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None
    files: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    createdAt: str
    matchSources: list[Literal["keyword", "vector"]] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: SearchMode = "keyword"
    limit: int = Field(default=10, ge=1, le=50)
    scope: MemoryScope | None = None
    project: str | None = None
    projectId: str | None = None
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
    scope: MemoryScope = "project"
    project: str | None = None
    projectId: str | None = None
    cwd: str | None = None
    language: Language | None = None
    sourceTypes: list[SourceType] = Field(default_factory=list)
    minScore: float | None = Field(default=None, ge=0.0)
    matchMode: SearchMatchMode = "auto"


class ContextResponse(BaseModel):
    query: str
    context: str
    sections: list["ContextSection"] = Field(default_factory=list)
    project: "ProjectRecord | None" = None
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


class MaintenanceRunRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=500)
    retryFailed: bool = True
    project: str | None = None
    projectId: str | None = None


class MaintenanceRunResponse(BaseModel):
    index: dict[str, Any] = Field(default_factory=dict)
    wiki: dict[str, Any] = Field(default_factory=dict)
    llm: dict[str, Any] = Field(default_factory=dict)
    pageCompression: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class ProjectRecord(BaseModel):
    id: str
    name: str
    root: str
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    createdAt: str
    updatedAt: str


class ProjectProfileRecord(BaseModel):
    id: str
    projectId: str
    project: str
    content: str
    goals: list[str] = Field(default_factory=list)
    techStack: list[str] = Field(default_factory=list)
    keyFiles: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    conventions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    sourceIds: list[str] = Field(default_factory=list)
    confidence: float | None = None
    createdAt: str
    updatedAt: str


class PinnedMemoryRecord(BaseModel):
    id: str
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None
    content: str
    sourceIds: list[str] = Field(default_factory=list)
    priority: int = Field(default=100, ge=0, le=1000)
    enabled: bool = True
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    createdAt: str
    updatedAt: str


class PinMemoryRequest(BaseModel):
    content: str = Field(min_length=1)
    scope: MemoryScope = "global"
    project: str | None = None
    projectId: str | None = None
    sourceIds: list[str] = Field(default_factory=list)
    priority: int = Field(default=100, ge=0, le=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class PinMemoryResponse(BaseModel):
    pinned: PinnedMemoryRecord


class ProjectProfileUpdateRequest(BaseModel):
    project: str | None = None
    projectId: str | None = None
    cwd: str | None = None
    limit: int = Field(default=25, ge=1, le=500)


class ProjectProfileUpdateResponse(BaseModel):
    project: ProjectRecord
    profile: ProjectProfileRecord


class ContextSection(BaseModel):
    name: ContextSectionName
    title: str
    content: str = ""
    empty: bool = False
    sourceIds: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
