## 1. Search Relevance

- [x] 1.1 Extend search request models and CLI/REST parsing with optional `minScore` and `matchMode`.
- [x] 1.2 Implement keyword relevance modes: `auto`, `any`, `all`, and `phrase`.
- [x] 1.3 Add vector result score thresholding and normalize vector scores for filtering.
- [x] 1.4 Implement hybrid rerank that boosts keyword+vector matches and demotes weak generic keyword-only matches.
- [x] 1.5 Ensure smart-search and context use only relevance-gated evidence.

## 2. Wiki Knowledge Quality

- [x] 2.1 Add compatible fields for distilled knowledge fingerprint, reinforcement metadata, and crystal source group.
- [x] 2.2 Implement deterministic fingerprinting and exact dedupe before saving knowledge.
- [x] 2.3 Implement conservative lesson reinforcement without losing source ids.
- [x] 2.4 Implement stable crystal source group handling to avoid duplicate crystals across topic rebuilds.
- [x] 2.5 Update Wiki rebuild to reuse existing distilled knowledge and distill only missing evidence.

## 3. Context Identity

- [x] 3.1 Add a unified AgentMemory context envelope to non-JSON `agentmemory context` output.
- [x] 3.2 Keep `[AgentMemory Context]`, `[Evidence]`, confidence, compressed state, and compact source ids in prompt output.
- [x] 3.3 Explicitly state that injected memory is external evidence, not system/developer/user instructions and cannot override current instructions.
- [x] 3.4 Preserve existing `agentmemory context --json` response shape.

## 4. Docs And Skill

- [x] 4.1 Update `skills/agentmemory/SKILL.md` with relevance, confidence, evidence, and identity-boundary guidance.
- [x] 4.2 Update `PROJECT.md` to replace待优化 notes with implemented relevance and Wiki quality behavior.
- [x] 4.3 Update OpenSpec main specs when archiving so search, wiki, context, and skill stay in sync.

## 5. Tests And Validation

- [x] 5.1 Add search tests for generic noisy queries, strict match modes, minScore, and hybrid rerank.
- [x] 5.2 Add smart-search/context tests proving weak evidence is filtered.
- [x] 5.3 Add Wiki tests for knowledge dedupe, lesson reinforcement, and stable crystal source groups.
- [x] 5.4 Add CLI tests for context envelope and unchanged `--json`.
- [x] 5.5 Run `uv run pytest` and `openspec validate improve-memory-quality-and-identity --strict`.
