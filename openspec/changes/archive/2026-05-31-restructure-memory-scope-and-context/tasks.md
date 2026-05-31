## 1. Scope And Project Models

- [x] 1.1 Add `MemoryScope`, `ProjectRecord`, scoped fields and context section models
- [x] 1.2 Add StateKV scopes for projects, project profiles and pinned memory
- [x] 1.3 Implement project identity resolution from `realpath(cwd)` root path
- [x] 1.4 Update export/import models to include projects, scope and projectId

## 2. Scoped Core Writes

- [x] 2.1 Make session start/observe upsert and attach ProjectRecord
- [x] 2.2 Make observations and summaries inherit scope/project identity
- [x] 2.3 Make explicit memories support global/project scope
- [x] 2.4 Make knowledge, insights and wiki pages preserve scope/project identity
- [x] 2.5 Implement internal project current session resolution for observe when sessionId is omitted
- [x] 2.6 Add configurable session TTL and stale session handling
- [x] 2.7 Add migration/default handling for records missing scope/projectId

## 3. Pinned Memory

- [x] 3.1 Implement pinned memory create/list/disable/delete service methods
- [x] 3.2 Add CLI commands for pinned memory management
- [x] 3.3 Add REST endpoints for pinned memory management
- [x] 3.4 Make context include enabled global and project pinned items first

## 4. Project Profile

- [x] 4.1 Implement project list/show service methods and interfaces
- [x] 4.2 Add LLM provider prompt for project profile update
- [x] 4.3 Implement project profile update from existing profile plus scoped evidence
- [x] 4.4 Add CLI and REST interfaces for profile read/update
- [x] 4.5 Include project profile in context and maintenance run

## 5. Scoped Search And Wiki

- [x] 5.1 Extend search request/result filtering with scope, projectId and optional sessionId
- [x] 5.2 Make project searches include global plus current project records by default
- [x] 5.3 Update search document mapping to index scope/projectId/sessionId consistently
- [x] 5.4 Make wiki consolidation operate in requested scope/project
- [x] 5.5 Make wiki synthesis available to context as a stable section

## 6. Fixed Agent Context Format

- [x] 6.1 Add context sections to response models while preserving compatible legacy fields
- [x] 6.2 Rewrite context packing to fixed order: identity, global, project, wiki-synthesis, lessons-and-crystals, recent-evidence, evidence
- [x] 6.3 Ensure agent-facing sections use LLM synthesis or existing synthesized records where applicable
- [x] 6.4 Update CLI prompt output to emit the fixed XML-like envelope and explicit empty sections
- [x] 6.5 Keep search/list/debug outputs raw and structured, without forced LLM rewriting

## 7. Skill And Docs

- [x] 7.1 Update Skill to explain global/project scope, project cwd resolution, optional internal session behavior, pinned memory and project profile
- [x] 7.2 Update README and technical docs with the new context architecture
- [x] 7.3 Update examples and acceptance commands for scoped context

## 8. Tests And Validation

- [x] 8.1 Add service tests for project upsert, scoped records and migration defaults
- [x] 8.2 Add service/CLI/REST tests for pinned memory and project profile
- [x] 8.3 Add search tests for global + project filtering and session filtering
- [x] 8.4 Add context tests for fixed sections, LLM synthesis priority and raw evidence preservation
- [x] 8.5 Add wiki tests for scoped consolidation and synthesis context
- [x] 8.6 Run pytest and strict OpenSpec validation
