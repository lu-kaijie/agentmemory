## Why

AgentMemory already stores memories, distilled knowledge, Wiki pages, and searchable evidence, but agents still need a stable way to turn those sources into compact prompt-ready context. This change adds a dedicated context capability so task startup and follow-up reasoning can use grounded memory without manually stitching together search results.

## What Changes

- Add a `context` command and API that accept a query plus packing options and return agent-injectable context.
- Build context from hybrid retrieval across memories, summaries, distilled knowledge, and Wiki pages.
- Prefer distilled knowledge and Wiki pages for durable context while preserving raw evidence references.
- Include structured evidence, grouped source summaries, confidence, and truncation/compression metadata in the response.
- Use the LLM provider to compress context when selected evidence exceeds the requested token budget.
- Update agent skill guidance so agents know when to call context instead of raw search or smart-search.

## Capabilities

### New Capabilities

- `memory-context`: Generates compact, evidence-grounded context from searchable memory sources for agent prompt injection.

### Modified Capabilities

- `agent-skill`: Documents when agents should use `agentmemory context` and how to treat its evidence and confidence.

## Impact

- Core models and service methods for context request/response and context packing.
- CLI command `agentmemory context`.
- REST endpoint `POST /agentmemory/context`.
- Search integration over `memory`, `summary`, `knowledge`, and `wikiPage` source types.
- LLM provider `compress_context` usage for token-budgeted output.
- Tests for service, CLI/API behavior, source filtering, confidence, and compression.
