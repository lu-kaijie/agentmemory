## 1. State And Index Helpers

- [x] 1.1 Add StateKV/core helpers to list all observations across sessions for export.
- [x] 1.2 Add StateKV/core helpers to delete a memory by id and return the deleted record snapshot.
- [x] 1.3 Add index helper to delete searchable document, FTS5 row and LanceDB vector rows by source type/id.
- [x] 1.4 Add tests for deleting memory index records and ensuring deleted memories are not returned by search.

## 2. Governance Service

- [x] 2.1 Implement export service returning version, exportedAt, sessions, observations, memories, summaries, memoryCandidates, llmProcessingJobs, indexJobs and audit.
- [x] 2.2 Ensure export payload never includes provider API keys or REST secret values.
- [x] 2.3 Implement forget service accepting memoryId and optional reason.
- [x] 2.4 Write audit action `export` on successful export.
- [x] 2.5 Write audit action `forget` on successful memory deletion.
- [x] 2.6 Return structured not found errors for missing memory ids without writing success audit.

## 3. REST API

- [x] 3.1 Add `GET /agentmemory/export`.
- [x] 3.2 Add `POST /agentmemory/forget`.
- [x] 3.3 Add REST tests for export shape, secret redaction, successful forget and missing memory forget.

## 4. CLI

- [x] 4.1 Add `agentmemory export` with `--json` output.
- [x] 4.2 Add `agentmemory forget --memory-id <id>` with optional `--reason`.
- [x] 4.3 Add CLI tests for export JSON and forget output.

## 5. Verification

- [x] 5.1 Run `uv run pytest`.
- [x] 5.2 Manually verify export contains current records and an export audit entry.
- [x] 5.3 Manually verify remembered memory can be searched before forget and is absent from memories, keyword search, vector search and hybrid search after forget.
