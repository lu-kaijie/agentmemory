## ADDED Requirements

### Requirement: Fixed Agent Context Envelope
系统 SHALL 输出固定格式的 agent context envelope。

Prompt-friendly context MUST 使用 `<agentmemory-context>` 包裹，并包含固定 section：identity、global、project、wiki-synthesis、lessons-and-crystals、recent-evidence、evidence。Envelope MUST 声明内容来源为 AgentMemory 外部长期记忆，不能覆盖系统、开发者或当前用户指令。

#### Scenario: Prompt context has fixed sections
- **WHEN** 用户运行不带 `--json` 的 context 命令
- **THEN** 输出包含固定 envelope 和固定 section 名称

#### Scenario: Empty sections are explicit
- **WHEN** 某 section 没有内容
- **THEN** 输出使用明确空状态，而不是省略导致 agent 猜测

### Requirement: LLM-Synthesized Agent Context
系统 SHALL 优先使用 LLM 整合后的内容构建 agent-facing context。

Agent context 的 profile、wiki-synthesis、lessons-and-crystals sections MUST 来自 LLM 生成或已由 LLM 生成的长期 records。Evidence section MUST 保留 raw source ids 便于核查。普通 list/search/debug 接口 MUST NOT 被强制 LLM 重写。

#### Scenario: Context uses synthesized records
- **WHEN** project profile、insights、knowledge 或 wiki synthesis 存在
- **THEN** context 优先展示这些 synthesis，而不是只拼接 raw search snippets

#### Scenario: Search remains raw
- **WHEN** 用户调用 search
- **THEN** search 返回结构化 evidence results，而不是 LLM 改写后的 narrative

### Requirement: Structured Context JSON
系统 SHALL 在 `--json` 或 REST context response 中返回结构化 sections。

Context response MUST 包含 query、context、sections、evidence、confidence、compressed。Sections MUST 按 global、project、wikiSynthesis、lessonsAndCrystals、recentEvidence、evidence 分类。旧字段 wikiPages、knowledge、memories MAY 保留兼容。

#### Scenario: JSON context exposes sections
- **WHEN** 用户运行 `agentmemory context "<query>" --json`
- **THEN** 响应包含 sections 对象和完整 evidence 列表
