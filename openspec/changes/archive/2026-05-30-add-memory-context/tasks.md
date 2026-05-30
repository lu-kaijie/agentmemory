## 1. Models And Core Context Builder

- [x] 1.1 Add `ContextRequest` and `ContextResponse` models with query, tokenBudget, limit, filters, grouped sources, evidence, confidence, and compressed fields.
- [x] 1.2 Add a core service method that retrieves context evidence with hybrid search and default sourceTypes `knowledge`, `wikiPage`, `memory`, and `summary`.
- [x] 1.3 Implement deterministic context packing that prioritizes knowledge and Wiki pages, preserves source ids, and groups response lists.
- [x] 1.4 Implement token budget handling with LLM `compress_context` when available and deterministic truncation when unavailable.
- [x] 1.5 Add a deterministic confidence heuristic based on result count, score strength, source diversity, and no-evidence state.

## 2. CLI And REST Interfaces

- [x] 2.1 Add `agentmemory context "<query>" --json` with tokenBudget, limit, project, language, and sourceTypes options.
- [x] 2.2 Add `POST /agentmemory/context` that returns the same response shape as the CLI.
- [x] 2.3 Ensure context source type parsing accepts `knowledge`, `wikiPage`, `memory`, `summary`, and explicit `observation`.

## 3. Agent Skill Guidance

- [x] 3.1 Update `skills/agentmemory/SKILL.md` to document when to use context at task start and when to use search or smart-search instead.
- [x] 3.2 Update Skill supported-operation guidance so context and wiki are listed as available operations while unsupported Hook/MCP integrations remain excluded.

## 4. Tests And Validation

- [x] 4.1 Add service tests for default retrieval, source type filtering, grouped response lists, no-evidence behavior, confidence, and compression/truncation.
- [x] 4.2 Add REST and CLI tests for context request/response JSON.
- [x] 4.3 Add or update skill/spec validation tests for context guidance.
- [x] 4.4 Run `uv run pytest` and `openspec validate add-memory-context --strict`.
