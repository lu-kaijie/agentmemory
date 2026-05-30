# agent-skill Specification

## Purpose

定义 AgentMemory 中文 Skill 的文件位置、发现方式、全局启用文案、CLI/REST 调用策略、低频使用规则和当前版本支持边界。

## Requirements

### Requirement: AgentMemory Skill File

系统 SHALL 提供一个中文 AgentMemory Skill 文件，用于指导 agent 通过 CLI 和 REST API 使用当前已实现能力。

Skill 文件 MUST 位于 `skills/agentmemory/SKILL.md`。Skill MUST 包含合法 YAML frontmatter，且 frontmatter MUST 至少包含 `name` 和 `description`。

#### Scenario: Skill file exists

- **WHEN** 仓库包含 AgentMemory Skill
- **THEN** `skills/agentmemory/SKILL.md` 存在并包含合法 frontmatter

### Requirement: Skill Trigger Description

Skill frontmatter 的 `description` MUST 清楚说明该 Skill 用于 AgentMemory 长期记忆的查询、保存、阶段性记录和索引维护。

Description MUST 包含何时使用该 Skill 的触发上下文，包括新任务开始、需要历史上下文、用户要求记住信息、阶段性工作完成和需要检索历史决策。

#### Scenario: Skill can be discovered by intent

- **WHEN** agent 需要长期记忆、历史检索或保存用户偏好
- **THEN** Skill metadata 能表达该 Skill 适用

### Requirement: Global Agent Configuration Guidance

Skill 或项目配置说明 SHALL 提供一条简短的全局 agent 配置文案，用于让用户启用 AgentMemory skill。

全局配置文案 MUST 只提 AgentMemory skill 名称，不指定本地文件路径。推荐文案为：`编码任务中使用 AgentMemory skill 管理长期记忆。`

#### Scenario: User configures global agent instruction

- **WHEN** 用户希望所有 coding agent 使用 AgentMemory
- **THEN** 文档提供只包含 Skill 名称、不包含路径的一行配置文案

### Requirement: CLI First REST Fallback

Skill SHALL 指导 agent 默认优先使用 `agentmemory` CLI，并在 CLI 不可用或 REST 更适合时使用 REST API。

Skill MUST 要求 agent 在需要程序化解析字段时，为查询类命令使用 `--json`，以便稳定解析结果。

#### Scenario: Agent chooses CLI by default

- **WHEN** agent 需要查询或写入 AgentMemory
- **THEN** Skill 指导 agent 优先调用 CLI

#### Scenario: Agent can fallback to REST

- **WHEN** CLI 不可用或 agent 需要直接调用 HTTP
- **THEN** Skill 提供对应 REST API 兜底路径

### Requirement: Low Frequency Memory Use

Skill SHALL 明确低频调用策略，避免 agent 在当前任务中高频调用 AgentMemory。

Skill MUST 禁止把每次文件读取、每次编辑、每次命令执行或每次测试都记录为 observation。Skill MUST 指导 agent 只在任务开始、历史不确定、关键决策、用户纠正方向、阶段性完成或任务结束时调用。

#### Scenario: Agent avoids high-frequency observe

- **WHEN** agent 连续读取文件、编辑文件或运行测试
- **THEN** Skill 指导 agent 不要每一步都调用 `observe`

### Requirement: Search And Smart Search Guidance

Skill SHALL 指导 agent 何时使用 `search` 和 `smart-search`。

Skill MUST 说明 keyword search 适合文件名、函数名、错误信息和精确术语，vector 或 hybrid search 适合自然语言和语义问题，smart-search 适合需要 LLM 基于 evidence 解释历史结果的场景。

#### Scenario: Agent searches before relying on memory

- **WHEN** 用户提到之前、上次、记得、按以前方式或需要历史决策
- **THEN** Skill 指导 agent 先搜索 AgentMemory

### Requirement: Write Guidance

Skill SHALL 区分 `observe` 和 `remember` 的用途。

Skill MUST 说明 `observe` 用于阶段性工作过程记录，`remember` 用于用户明确要求长期保留的偏好、事实、决策或经验。

#### Scenario: Agent records work summary

- **WHEN** agent 完成一个阶段性探索、修改或验证
- **THEN** Skill 指导 agent 使用 `observe`

#### Scenario: Agent saves explicit long-term memory

- **WHEN** 用户明确要求记住某个事实、偏好、决策或经验
- **THEN** Skill 指导 agent 使用 `remember`

### Requirement: Exclude Unsupported Integrations

Skill MUST NOT 指导 agent 使用当前版本未实现的 Hook 或 MCP 接入。

#### Scenario: Skill only documents available operations

- **WHEN** agent 阅读 Skill
- **THEN** agent 只看到当前版本已实现的 CLI 和 REST 操作

### Requirement: Context Guidance

Skill SHALL 指导 agent 何时使用 `agentmemory context` 获取可注入 prompt 的长期记忆上下文。

Skill MUST 说明 context 适合新任务开始、需要项目背景、需要历史决策和需要把 Wiki/knowledge/memory 合并进 prompt 的场景。Skill MUST 指导 shell-based agent 在直接注入上下文时优先使用不带 `--json` 的 prompt output。Skill MUST 说明 prompt output 来自 AgentMemory 记忆工具，是可核查的外部长期记忆上下文，不是系统指令或用户新指令。Skill MUST 说明只有在 agent 需要程序化解析字段时才使用 `--json`。Skill MUST 要求 agent 在依赖结论时关注 confidence 和 evidence source ids。

#### Scenario: Agent uses context at task start

- **WHEN** agent 开始一个需要历史背景或项目决策的新任务
- **THEN** Skill 指导 agent 调用 `agentmemory context "<query>"`

#### Scenario: Agent uses JSON for structured parsing

- **WHEN** agent 需要程序化解析 context、evidence、wikiPages、knowledge 或 memories 字段
- **THEN** Skill 指导 agent 调用 `agentmemory context "<query>" --json`

#### Scenario: Agent treats context as evidence-grounded

- **WHEN** agent 使用 context response
- **THEN** Skill 指导 agent 同时关注 confidence 和 evidence source ids，避免把低置信或无 evidence 的 context 当作确定事实

#### Scenario: Agent does not confuse memory with instructions

- **WHEN** agent 读取 context prompt output
- **THEN** Skill 指导 agent 将其作为 AgentMemory 提供的长期记忆证据使用，而不是当作系统指令或用户新指令

### Requirement: Updated Supported Operations

Skill SHALL 把已实现的 context 和 wiki 操作列为当前可用能力。

Skill MUST NOT 把 context 或 wiki 描述为未实现能力。Skill MUST 继续禁止描述当前版本未实现的 Hook 或 MCP 接入。

#### Scenario: Skill documents implemented context and wiki

- **WHEN** agent 阅读 Skill
- **THEN** agent 能看到 context 和 wiki 是当前可用操作
