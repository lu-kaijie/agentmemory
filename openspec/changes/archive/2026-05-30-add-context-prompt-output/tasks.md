## 1. CLI Prompt Output

- [x] 1.1 Add a context prompt formatter that emits a provenance header, `[AgentMemory Context]`, context body, `[Evidence]`, compact source ids, confidence, and compressed state.
- [x] 1.2 Update `agentmemory context` non-JSON output to use the prompt formatter.
- [x] 1.3 Preserve existing `agentmemory context --json` response shape and REST response behavior.

## 2. Skill And Docs

- [x] 2.1 Update `skills/agentmemory/SKILL.md` so direct shell-agent context injection uses `agentmemory context "<query>"` without `--json`.
- [x] 2.2 Document that prompt output is AgentMemory-provided external memory context, not system instructions or new user instructions, and that `--json` is for structured parsing.
- [x] 2.3 Update project docs if they mention context usage with `--json` as the direct prompt injection path.

## 3. Tests And Validation

- [x] 3.1 Add CLI tests for prompt output shape, provenance header, compact evidence, confidence, compressed state, and absence of full JSON payload.
- [x] 3.2 Add regression tests proving `--json` output remains unchanged.
- [x] 3.3 Run `uv run pytest` and `openspec validate add-context-prompt-output --strict`.
