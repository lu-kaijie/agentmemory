## 1. Local Development

- [x] 1.1 Add `.env.example` with local database, vector, LLM, embedding and maintenance settings
- [x] 1.2 Add `scripts/dev.sh` and `scripts/test.sh`
- [x] 1.3 Document local scripts in PROJECT.md

## 2. Maintenance Core

- [x] 2.1 Add maintenance settings and health/config summary fields
- [x] 2.2 Add maintenance response models
- [x] 2.3 Implement core maintenance run for index repair, failed LLM retry and Wiki retry
- [x] 2.4 Add Wiki failed job retry and conservative pending job merge

## 3. Interfaces And Scheduler

- [x] 3.1 Add `agentmemory maintenance run --json`
- [x] 3.2 Add `POST /agentmemory/maintenance/run`
- [x] 3.3 Add configurable FastAPI maintenance worker
- [x] 3.4 Add optional REST envelope support without breaking default responses

## 4. Tests And Docs

- [x] 4.1 Add tests for scripts/env example and maintenance settings
- [x] 4.2 Add service tests for failed LLM retry, index retry and Wiki retry
- [x] 4.3 Add CLI/REST tests for maintenance and REST envelope
- [x] 4.4 Update build task progress for 1.4, 4.5, 6.1 and 8.4
- [x] 4.5 Run pytest and strict OpenSpec validation
