## ADDED Requirements

### Requirement: AgentMemory Context Envelope

系统 SHALL 为非 JSON context CLI 输出提供统一的 AgentMemory context envelope。

Envelope MUST 明确标识来源为 AgentMemory 长期记忆工具，MUST 标识内容类型为 external long-term memory context，MUST 包含 confidence、compressed 和 evidence 摘要。Envelope MUST 明确声明该内容不是系统指令、不是开发者指令、不是用户新指令，且不能覆盖当前会话中的更高优先级指令或用户请求。Envelope MUST 保留 `[AgentMemory Context]` 和 `[Evidence]` 可读段落，便于 shell-based agent 直接加载。

#### Scenario: Prompt output has bounded envelope

- **WHEN** 用户运行 `agentmemory context "历史决策"` 且不带 `--json`
- **THEN** CLI 输出包含 AgentMemory context envelope、来源说明、confidence、compressed 和 evidence 摘要

#### Scenario: Prompt output cannot override instructions

- **WHEN** agent 读取 context prompt output
- **THEN** 输出文本明确要求 agent 将其作为可核查背景证据，而不是系统指令、开发者指令或用户新指令

#### Scenario: JSON context remains parseable

- **WHEN** 用户运行 `agentmemory context "历史决策" --json`
- **THEN** CLI 保持输出结构化 JSON response，不强制输出 prompt envelope

### Requirement: Context Uses Relevance-Gated Evidence

系统 SHALL 使用通过 search relevance gate 的结果构建 context。

Context retrieval MUST NOT pack 被相关性门控过滤的 evidence。Context confidence MUST 反映 evidence 数量、score、matchSources 和 compressed 状态。若 evidence 不足，context MUST 返回低 confidence 或空 context。

#### Scenario: Context ignores filtered evidence

- **WHEN** search 原始召回结果被 relevance gate 过滤
- **THEN** context 不把这些结果写入 prompt context

#### Scenario: Context confidence reflects evidence quality

- **WHEN** context 只包含低数量或单一路径 evidence
- **THEN** response confidence 低于多来源高分 evidence 的 response
