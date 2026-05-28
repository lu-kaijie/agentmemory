from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Language = Literal["zh", "en", "mixed", "unknown"]


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


class AuditRecord(BaseModel):
    id: str
    action: Literal["observe", "remember"]
    targetType: Literal["observation", "memory"]
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

