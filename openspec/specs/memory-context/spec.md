# memory-context Specification

## Purpose

定义 AgentMemory 将搜索、distilled knowledge、Wiki 页面和长期记忆打包成 agent 可注入上下文的能力。

## Requirements

### Requirement: Build Agent Context

系统 SHALL 基于查询生成可注入 agent prompt 的 memory context。

Context response MUST 包含 `query`、`context`、`evidence`、`wikiPages`、`knowledge`、`memories`、`confidence` 和 `compressed`。`evidence` MUST 保留每条来源的 `sourceType`、`sourceId`、`content`、`score` 和 `matchSources`。

#### Scenario: Build context from matching sources

- **WHEN** 客户端提交 context query
- **THEN** 系统返回包含 context 文本和 evidence source ids 的响应

#### Scenario: No context evidence

- **WHEN** 查询没有检索到任何可用 evidence
- **THEN** 系统返回空 context、空 evidence、confidence 为 `0` 且 compressed 为 `false`

### Requirement: Context Retrieval Defaults

系统 SHALL 默认使用 hybrid search 检索 context evidence。

默认 source types MUST 为 `knowledge`、`wikiPage`、`memory` 和 `summary`。系统 MUST 支持通过 `sourceTypes` 覆盖默认来源。系统 MUST 支持 `project` 和 `language` 过滤。

#### Scenario: Context prefers durable sources

- **WHEN** 客户端没有指定 sourceTypes
- **THEN** 系统从 knowledge、wikiPage、memory 和 summary 中检索 evidence，且不默认包含 observation

#### Scenario: Context honors source type filter

- **WHEN** 客户端指定 sourceTypes 为 `wikiPage` 和 `knowledge`
- **THEN** 系统只返回 wikiPage 和 knowledge evidence

#### Scenario: Context honors metadata filters

- **WHEN** 客户端指定 project 或 language
- **THEN** 系统只使用符合过滤条件的 evidence 构建 context

### Requirement: Context Packing

系统 SHALL 将检索到的 evidence 打包为稳定、可读、可注入 prompt 的 context 文本。

Packing MUST 优先包含 `knowledge` 和 `wikiPage`，再包含 `memory` 和 `summary`。Context 文本 MUST 标注来源 id，避免 agent 把未引用内容当作已验证事实。

#### Scenario: Pack context in source priority order

- **WHEN** 检索结果同时包含 knowledge、wikiPage、memory 和 summary
- **THEN** context 文本优先展示 knowledge 和 wikiPage 内容，并保留每段来源 id

#### Scenario: Preserve grouped response lists

- **WHEN** context response 包含多种 sourceType
- **THEN** 系统分别填充 wikiPages、knowledge 和 memories 列表，供 agent 结构化读取

### Requirement: Token Budget And Compression

系统 SHALL 支持通过 `tokenBudget` 控制 context 长度。

当打包后的 context 超过 tokenBudget 且 LLM provider 可用时，系统 MUST 调用 `compress_context` 压缩 context。当 LLM provider 不可用时，系统 MUST 使用确定性截断。压缩或截断 MUST NOT 删除 structured evidence。

#### Scenario: Compress oversized context with LLM

- **WHEN** 打包后的 context 超过 tokenBudget 且 LLM provider 可用
- **THEN** 系统调用 `compress_context` 并返回 compressed 为 `true`

#### Scenario: Truncate oversized context without LLM

- **WHEN** 打包后的 context 超过 tokenBudget 且 LLM provider 不可用
- **THEN** 系统返回确定性截断后的 context，并保留完整 evidence 列表

### Requirement: Context Interfaces

系统 SHALL 提供 CLI 和 REST 接口生成 memory context。

CLI MUST 提供 `agentmemory context "<query>" --json`。REST MUST 提供 `POST /agentmemory/context`。两个接口 MUST 支持 `query`、`tokenBudget`、`limit`、`project`、`language` 和 `sourceTypes`。

#### Scenario: Generate context from CLI

- **WHEN** 用户运行 `agentmemory context "历史决策" --json`
- **THEN** CLI 输出 context response JSON

#### Scenario: Generate context from REST

- **WHEN** 客户端 POST `/agentmemory/context`
- **THEN** API 返回 context response JSON
