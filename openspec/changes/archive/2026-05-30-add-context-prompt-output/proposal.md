## Why

`agentmemory context --json` is useful for programmatic integrations, but shell-based agents such as Claude Code or Codex may place the whole command output into their working context instead of parsing only the `context` field. A prompt-focused output mode will make context retrieval safer and cheaper for agents that consume plain command output.

## What Changes

- Add a prompt-oriented output mode for `agentmemory context`.
- Keep JSON output unchanged for programmatic callers.
- Format prompt output as concise text with an explicit context section, compact evidence references, confidence, and compression metadata.
- Update Skill guidance so shell agents prefer prompt output and use `--json` only when they need structured parsing.
- Add tests that ensure prompt output does not include full JSON payload duplication.

## Capabilities

### New Capabilities

### Modified Capabilities

- `memory-context`: Add prompt-friendly CLI output for context responses while preserving existing JSON and REST behavior.
- `agent-skill`: Guide agents to choose prompt output for direct context injection and JSON output for structured integrations.

## Impact

- CLI output formatting for `agentmemory context`.
- Skill documentation and project docs that describe how agents consume context.
- Tests for prompt output shape, evidence references, and continued JSON compatibility.
