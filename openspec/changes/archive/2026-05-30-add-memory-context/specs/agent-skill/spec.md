## ADDED Requirements

### Requirement: Context Guidance

Skill SHALL 指导 agent 何时使用 `agentmemory context` 获取可注入 prompt 的长期记忆上下文。

Skill MUST 说明 context 适合新任务开始、需要项目背景、需要历史决策和需要把 Wiki/knowledge/memory 合并进 prompt 的场景。Skill MUST 要求 agent 优先使用 context response 中的 `context` 字段，并在依赖结论时保留或查看 evidence source ids。

#### Scenario: Agent uses context at task start

- **WHEN** agent 开始一个需要历史背景或项目决策的新任务
- **THEN** Skill 指导 agent 调用 `agentmemory context "<query>" --json`

#### Scenario: Agent treats context as evidence-grounded

- **WHEN** agent 使用 context response
- **THEN** Skill 指导 agent 同时关注 confidence 和 evidence source ids，避免把低置信或无 evidence 的 context 当作确定事实

### Requirement: Updated Supported Operations

Skill SHALL 把已实现的 context 和 wiki 操作列为当前可用能力。

Skill MUST NOT 把 context 或 wiki 描述为未实现能力。Skill MUST 继续禁止描述当前版本未实现的 Hook 或 MCP 接入。

#### Scenario: Skill documents implemented context and wiki

- **WHEN** agent 阅读 Skill
- **THEN** agent 能看到 context 和 wiki 是当前可用操作
