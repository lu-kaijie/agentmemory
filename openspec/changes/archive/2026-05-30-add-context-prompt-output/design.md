## Context

The context capability now returns structured JSON and the CLI prints only `response.context` when `--json` is omitted. That is usable, but it does not expose compact evidence ids or confidence in plain text, and Skill still points agents toward `--json`.

For shell-based agents, a prompt-ready text shape should be the default direct-consumption path. The JSON contract remains the integration path for programs that parse fields.

## Goals / Non-Goals

**Goals:**

- Provide a stable prompt-oriented CLI output for `agentmemory context`.
- Include context text, compact evidence references, confidence, and compression metadata without duplicating full JSON.
- Keep `--json` response shape unchanged.
- Update Skill guidance to distinguish direct prompt use from structured parsing.

**Non-Goals:**

- Change REST API behavior.
- Change retrieval, ranking, compression, or confidence logic.
- Add a new storage model or provider method.
- Solve automatic hook/MCP injection.

## Decisions

1. Keep `--json` as the only JSON output switch.

   Rationale: Existing commands use `--json`; preserving that convention avoids breaking programmatic callers.

   Alternative considered: Add `--format json|prompt`. This is more explicit but overlaps with the existing boolean convention and increases CLI surface for a small change.

2. Make non-JSON context output a prompt block.

   Rationale: Without `--json`, the CLI is already intended for human/plain-text output. Making it prompt-ready lets shell agents consume the command output directly.

   Alternative considered: Add a separate `context prompt` subcommand. That splits one capability across commands and makes Skill guidance more complex.

3. Include only compact evidence metadata in prompt output.

   Rationale: Full evidence text duplicates context and can defeat token budget savings. Source ids, confidence, and compressed state are enough for prompt injection; structured callers can still use `--json`.

## Risks / Trade-offs

- Agents may still run `--json` and ingest full JSON → Skill will recommend plain output for direct context injection and reserve `--json` for parsing.
- Compact evidence ids may be insufficient for debugging → Users can rerun with `--json` to inspect full evidence.
- Changing non-JSON output affects humans used to context-only output → The new output remains readable and preserves the context as the first section.
