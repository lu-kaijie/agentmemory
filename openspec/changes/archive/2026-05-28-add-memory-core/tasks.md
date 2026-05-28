## 1. Models And Scopes

- [x] 1.1 Add core Pydantic models for Session, Observation, Memory, AuditRecord, and request/response payloads
- [x] 1.2 Extend KV scope helpers for sessions, observations by session, memories, and audit
- [x] 1.3 Add ID and timestamp utility helpers

## 2. Core Service

- [x] 2.1 Implement memory core service with `observe`
- [x] 2.2 Implement session create/update behavior during observation save
- [x] 2.3 Implement `remember`
- [x] 2.4 Implement audit write helper for observe and remember
- [x] 2.5 Implement list sessions, list memories, and list audit
- [x] 2.6 Add unit tests for observe, session update, remember, and audit

## 3. REST API

- [x] 3.1 Add memory core routes to FastAPI app
- [x] 3.2 Implement `POST /agentmemory/observe`
- [x] 3.3 Implement `POST /agentmemory/remember`
- [x] 3.4 Implement `GET /agentmemory/sessions`, `GET /agentmemory/memories`, and `GET /agentmemory/audit`
- [x] 3.5 Add REST integration tests for save and list endpoints

## 4. CLI

- [x] 4.1 Implement `agentmemory observe`
- [x] 4.2 Implement `agentmemory remember`
- [x] 4.3 Implement `agentmemory sessions`, `agentmemory memories`, and `agentmemory audit`
- [x] 4.4 Add `--json` support for list commands
- [x] 4.5 Add CLI tests for observe, remember, and list commands

## 5. Verification

- [x] 5.1 Run pytest for all tests
- [x] 5.2 Verify OpenSpec status remains complete
