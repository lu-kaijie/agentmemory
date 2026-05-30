## 1. Models And State

- [x] 1.1 Add Wiki page and Wiki update job Pydantic models.
- [x] 1.2 Add Wiki request/response models for list, update and rebuild operations.
- [x] 1.3 Add `KV.wikiPages` and `KV.wikiUpdateJobs` scopes.
- [x] 1.4 Extend audit model to support `wiki_update` action and `wiki_page` target type.
- [x] 1.5 Extend search source type to include `wikiPage`.
- [x] 1.6 Add distilled knowledge model and `KV.knowledge` scope.
- [x] 1.7 Extend audit and search source types for distilled knowledge.

## 2. LLM Wiki Processing

- [x] 2.1 Add LLM provider method for Wiki update proposal generation.
- [x] 2.2 Implement OpenAI-compatible Wiki prompt using XML-like output.
- [x] 2.3 Implement parser for Wiki update proposal tags.
- [x] 2.4 Add unit tests for valid and invalid Wiki proposal parsing.
- [x] 2.5 Add LLM provider method for knowledge distillation.
- [x] 2.6 Implement XML-like parser for semantic/procedural/lesson/crystal records.

## 3. Core Wiki Service

- [x] 3.1 Enqueue Wiki update job after observation save.
- [x] 3.2 Enqueue Wiki update job after memory save.
- [x] 3.3 Enqueue Wiki update job after summary save.
- [x] 3.4 Implement list Wiki pages and list Wiki jobs.
- [x] 3.5 Implement processing pending Wiki jobs.
- [x] 3.6 Implement Wiki rebuild by topic and rebuild all.
- [x] 3.7 Write `wiki_update` audit when a Wiki page is created or updated.
- [x] 3.8 Ensure failed Wiki processing preserves source data and records failed job state.
- [x] 3.9 Add core service tests for enqueue, apply, failure and rebuild.
- [x] 3.10 Distill semantic/procedural/lesson/crystal records before Wiki page update.
- [x] 3.11 Add list distilled knowledge support.

## 4. Search Indexing

- [x] 4.1 Add `wiki_page_document` searchable document builder.
- [x] 4.2 Index Wiki pages after successful create/update.
- [x] 4.3 Include Wiki pages in index rebuild/repair source documents.
- [x] 4.4 Add search tests for keyword/vector/hybrid Wiki page results and sourceTypes filtering.
- [x] 4.5 Index distilled knowledge and support `sourceTypes=["knowledge"]`.

## 5. REST API

- [x] 5.1 Add `GET /agentmemory/wiki/pages`.
- [x] 5.2 Add `GET /agentmemory/wiki/jobs`.
- [x] 5.3 Add `POST /agentmemory/wiki/update`.
- [x] 5.4 Add `POST /agentmemory/wiki/rebuild`.
- [x] 5.5 Add REST tests for list, update and rebuild.
- [x] 5.6 Add `GET /agentmemory/wiki/knowledge`.

## 6. CLI

- [x] 6.1 Add `agentmemory wiki pages`.
- [x] 6.2 Add `agentmemory wiki jobs`.
- [x] 6.3 Add `agentmemory wiki update`.
- [x] 6.4 Add `agentmemory wiki rebuild --topic <topic>` and `--all`.
- [x] 6.5 Add CLI tests for Wiki commands and JSON output.
- [x] 6.6 Add `agentmemory wiki knowledge`.

## 7. Viewer

- [x] 7.1 Add Viewer tab or section for Wiki pages.
- [x] 7.2 Add Viewer tab or section for Wiki update jobs.
- [x] 7.3 Ensure Viewer Wiki UI is read-only and does not expose edit/delete controls.
- [x] 7.4 Add Viewer/static content tests for Wiki endpoints and read-only constraints.
- [x] 7.5 Add Viewer read-only distilled knowledge tab.

## 8. Verification

- [x] 8.1 Run `uv run pytest`.
- [x] 8.2 Manually verify `agentmemory wiki rebuild --all --json` creates or updates Wiki pages.
- [x] 8.3 Manually verify Wiki pages appear in `agentmemory search` results.
- [x] 8.4 Manually verify Viewer displays Wiki pages and Wiki jobs.
- [x] 8.5 Update project and change docs to position Wiki pages as P0 entry for the broader LLM Wiki knowledge layer.
