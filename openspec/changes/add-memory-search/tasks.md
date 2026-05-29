## 1. Dependencies And Configuration

- [ ] 1.1 Add LanceDB dependency and any required test dependency updates
- [ ] 1.2 Add vector index configuration fields and defaults
- [ ] 1.3 Extend doctor/health status to include search index readiness

## 2. Models And Storage

- [ ] 2.1 Add SearchDocument, SearchResult, SearchRequest, SearchResponse, SmartSearchResponse, IndexJob, and IndexStatus models
- [ ] 2.2 Add StateKV scopes for search documents and index jobs
- [ ] 2.3 Add SQLite FTS5 schema setup and migration/probe logic
- [ ] 2.4 Add LanceDB table initialization and metadata schema

## 3. Indexing Service

- [ ] 3.1 Implement searchable document builders for observation, memory, and summary
- [ ] 3.2 Implement FTS5 insert/delete/search helpers
- [ ] 3.3 Implement LanceDB vector insert/delete/search helpers
- [ ] 3.4 Implement index job lifecycle: pending/running/done/failed
- [ ] 3.5 Implement soft-fail indexing behavior when embedding or LanceDB fails
- [ ] 3.6 Implement index status aggregation
- [ ] 3.7 Implement index rebuild from existing observations, memories, and summaries
- [ ] 3.8 Implement index repair for missing or failed jobs

## 4. Memory Core Integration

- [ ] 4.1 Inject indexing service or provider bundle into MemoryCoreService
- [ ] 4.2 Trigger observation indexing after observe save
- [ ] 4.3 Trigger summary indexing after LLM processing succeeds
- [ ] 4.4 Trigger memory indexing after remember save
- [ ] 4.5 Ensure indexing failures do not rollback source data

## 5. Search Service

- [ ] 5.1 Implement keyword search mode using FTS5
- [ ] 5.2 Implement vector search mode using embedding provider and LanceDB
- [ ] 5.3 Implement hybrid search mode with dedupe and combined ranking
- [ ] 5.4 Implement sourceType, project, language, and limit filtering
- [ ] 5.5 Implement smart-search LLM explanation with evidence/source ids
- [ ] 5.6 Implement no-results smart-search response

## 6. REST API

- [ ] 6.1 Add `POST /agentmemory/search`
- [ ] 6.2 Add `POST /agentmemory/smart-search`
- [ ] 6.3 Add `GET /agentmemory/index/status`
- [ ] 6.4 Add `POST /agentmemory/index/rebuild`
- [ ] 6.5 Add `POST /agentmemory/index/repair`
- [ ] 6.6 Add REST tests for search, smart-search, index status, rebuild, and repair

## 7. CLI

- [ ] 7.1 Add `agentmemory search`
- [ ] 7.2 Add `agentmemory smart-search`
- [ ] 7.3 Add `agentmemory index status`
- [ ] 7.4 Add `agentmemory index rebuild`
- [ ] 7.5 Add `agentmemory index repair`
- [ ] 7.6 Add CLI tests for JSON output and search modes

## 8. Verification

- [ ] 8.1 Add service tests for indexing on observe, summary, and remember
- [ ] 8.2 Add tests for embedding/LanceDB failure preserving source data
- [ ] 8.3 Add tests for FTS5 keyword search
- [ ] 8.4 Add tests for vector search with real embedding provider or controlled test vector provider
- [ ] 8.5 Add tests for hybrid dedupe and evidence preservation
- [ ] 8.6 Add documentation checks ensuring Wiki/Viewer/Hook/MCP are not part of this change
- [ ] 8.7 Run full pytest suite
- [ ] 8.8 Verify OpenSpec status is complete for `add-memory-search`
