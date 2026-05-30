## 1. Skill And Specs

- [x] 1.1 Update `skills/agentmemory/SKILL.md` with task-start context and task-end session summary guidance
- [x] 1.2 Update project docs and main build tasks after implementation

## 2. Core Session Lifecycle

- [x] 2.1 Extend core models for session status, endedAt, summaryId, session start/end requests and responses
- [x] 2.2 Implement `MemoryCoreService.start_session` and `MemoryCoreService.end_session`
- [x] 2.3 Generate session summaries from session observations and index them
- [x] 2.4 Enqueue Wiki update jobs from session summaries

## 3. Interfaces

- [x] 3.1 Add `agentmemory session start` and `agentmemory session end` CLI commands with JSON output
- [x] 3.2 Add `POST /agentmemory/session/start` and `POST /agentmemory/session/end` REST endpoints
- [x] 3.3 Update Viewer session display for status, endedAt and summaryId

## 4. Tests And Validation

- [x] 4.1 Add core service tests for start/end, empty session end and session summary searchability
- [x] 4.2 Add CLI and REST tests for session lifecycle
- [x] 4.3 Run pytest and strict OpenSpec validation
