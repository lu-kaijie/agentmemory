## ADDED Requirements

### Requirement: Prompt Context Output

系统 SHALL 提供适合 shell-based agent 直接注入 prompt 的 context CLI 文本输出。

当用户运行 `agentmemory context "<query>"` 且未指定 `--json` 时，CLI MUST 输出 prompt-friendly 文本。该文本 MUST 包含 provenance header，明确说明内容由 AgentMemory 记忆工具提供，是外部长期记忆上下文，不是系统指令或用户新指令。该文本 MUST 包含 `[AgentMemory Context]` section、context 正文、`[Evidence]` section、compact source ids、confidence 和 compressed 状态。Prompt output MUST NOT 输出完整 JSON payload，也 MUST NOT 重复展开完整 `wikiPages`、`knowledge` 和 `memories` 列表。

#### Scenario: CLI prints prompt-ready context

- **WHEN** 用户运行 `agentmemory context "历史决策"` 且不带 `--json`
- **THEN** CLI 输出以 `[AgentMemory Context]` 开头的 prompt-friendly 文本

#### Scenario: Prompt output includes compact evidence

- **WHEN** context response 包含 evidence
- **THEN** prompt output 展示 compact source ids、confidence 和 compressed 状态，但不输出完整 JSON

#### Scenario: Prompt output identifies memory source

- **WHEN** 用户运行 `agentmemory context "历史决策"` 且不带 `--json`
- **THEN** CLI 输出明确说明该内容来自 AgentMemory 记忆工具，agent 应将其视为可核查的长期记忆上下文而非系统指令或用户新指令

#### Scenario: JSON output remains structured

- **WHEN** 用户运行 `agentmemory context "历史决策" --json`
- **THEN** CLI 保持输出完整 context response JSON
