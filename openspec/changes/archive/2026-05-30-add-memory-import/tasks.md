## 1. Models And Core Import

- [x] 1.1 Add governance schemaVersion and import request/response models
- [x] 1.2 Implement `MemoryCoreService.import_data` with version validation and per-record validation
- [x] 1.3 Implement conservative id-based deduplication and imported/skipped/errors counters
- [x] 1.4 Write import audit with source, schemaVersion and summary counts

## 2. Index And Search Recovery

- [x] 2.1 Recreate searchable documents for imported observations, memories, summaries, knowledge and Wiki pages
- [x] 2.2 Ensure imported data can be found by search and context

## 3. CLI, REST And Docs

- [x] 3.1 Add `agentmemory import --file <path> --json`
- [x] 3.2 Add `POST /agentmemory/import`
- [x] 3.3 Update Skill and PROJECT.md with import/export compatibility guidance
- [x] 3.4 Update `build-agent-memory-platform` task 8.1 after implementation

## 4. Tests And Validation

- [x] 4.1 Add service tests for export/import into a fresh database
- [x] 4.2 Add CLI and REST tests for import success, duplicate skip and unsupported version
- [x] 4.3 Run pytest and strict OpenSpec validation
