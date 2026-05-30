## Context

AgentMemory already has searchable observations, memories, summaries, distilled knowledge, and Wiki pages. `smart-search` can explain search results, but it is answer-oriented and does not provide a stable contract for prompt injection at the start of an agent task.

The context capability should sit above search and below agent workflows. It retrieves evidence, ranks durable sources first, packs a concise context string, and preserves source ids so agents can cite or inspect supporting records.

## Goals / Non-Goals

**Goals:**

- Provide one CLI and REST entry point for prompt-ready memory context.
- Retrieve across `memory`, `summary`, `knowledge`, and `wikiPage` by default.
- Prefer durable knowledge and Wiki pages over raw records when packing context.
- Preserve evidence records with source ids, scores, and match sources.
- Respect a token budget and use the LLM provider to compress oversized context.
- Return enough metadata for agents to judge whether context is usable.

**Non-Goals:**

- Replace `search` or `smart-search`.
- Add new storage collections.
- Add new embedding or reranking dependencies.
- Implement retrieval relevance threshold tuning or knowledge deduplication.
- Mutate memories, knowledge, or Wiki pages while building context.

## Decisions

1. Add a dedicated `ContextRequest` / `ContextResponse` model.

   Rationale: Context output has a different contract from `SmartSearchResponse`. It needs packed text, grouped evidence, selected source lists, confidence, and compression metadata rather than an LLM answer.

   Alternative considered: Extend `smart-search`. That would blur answer generation and prompt injection, and would make future agent flows depend on a response shape designed for user-facing explanations.

2. Use existing hybrid search as the retrieval layer.

   Rationale: Search already supports keyword, vector, hybrid, source type filtering, project filtering, and language filtering. Reusing it avoids a second retrieval path and keeps index behavior consistent.

   Alternative considered: Query KV collections directly. That would lose ranking, search filters, and vector recall.

3. Default source types to `knowledge`, `wikiPage`, `memory`, and `summary`.

   Rationale: Distilled knowledge and Wiki pages are most compact and durable, while raw memories and summaries provide fallback evidence. Observations remain available only when explicitly requested to avoid noisy prompt context.

   Alternative considered: Include observations by default. That increases recall but tends to pack transient work logs into agent prompts.

4. Pack context deterministically before optional LLM compression.

   Rationale: The system should provide useful context without requiring an LLM. When content exceeds the token budget and an LLM is configured, `compress_context` can produce a smaller context while evidence remains unchanged.

   Alternative considered: Always use the LLM to synthesize context. That increases cost and makes offline usage weaker.

5. Confidence is derived from retrieved evidence, source diversity, and compression state.

   Rationale: Agents need a coarse signal for whether the returned context is strong enough to use. The first version can use a deterministic heuristic and expose it without making it a hard gate.

   Alternative considered: Ask the LLM to score confidence. That is more expensive and less predictable for a first implementation.

## Risks / Trade-offs

- Search may return loosely related evidence → Keep source ids and scores visible, and document that relevance tuning remains a separate optimization.
- Token budget estimation may be approximate → Use conservative character-based packing and LLM compression only when needed.
- Context could over-prefer Wiki pages that are stale → Preserve evidence freshness and source ids so agents can inspect raw records when needed.
- LLM compression may omit nuance → Keep uncompressed structured evidence in the response even when the `context` string is compressed.
