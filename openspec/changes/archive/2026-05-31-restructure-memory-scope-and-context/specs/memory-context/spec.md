## MODIFIED Requirements

### Requirement: Build Agent Context

系统 SHALL 基于查询生成可注入 agent prompt 的 memory context。

Context response MUST 包含 `query`、`context`、`sections`、`evidence`、`wikiPages`、`knowledge`、`memories`、`confidence` 和 `compressed`。`sections` MUST 按 Global / Project / Wiki Synthesis / Lessons And Crystals / Recent Evidence / Evidence 分类。`evidence` MUST 保留每条来源的 `sourceType`、`sourceId`、`content`、`score` 和 `matchSources`。

#### Scenario: Build context from matching sources

- **WHEN** 客户端提交 context query
- **THEN** 系统返回包含固定 sections、context 文本和 evidence source ids 的响应

#### Scenario: No context evidence

- **WHEN** 查询没有检索到任何可用 evidence 且无 pinned/profile/synthesis 内容
- **THEN** 系统返回空 context、空 evidence、confidence 为 `0` 且 compressed 为 `false`

### Requirement: Context Retrieval Defaults

系统 SHALL 默认使用 Global + Project scoped retrieval 构建 context。

默认 context MUST 先读取 global pinned/profile-like records，再读取当前 project 的 profile、pinned items、wiki synthesis、knowledge、insight、lesson、crystal 和 recent evidence。系统 MUST 支持通过 `sourceTypes` 覆盖 evidence 来源。系统 MUST 支持 `project`、`scope` 和 `language` 过滤。Context MUST NOT 要求用户显式 start session。

#### Scenario: Context prefers durable scoped sources

- **WHEN** 客户端没有指定 sourceTypes
- **THEN** 系统从 global records 和当前 project 的 synthesized/durable records 中构建 context，且不默认包含 raw observation

#### Scenario: Context honors source type filter

- **WHEN** 客户端指定 sourceTypes 为 `wikiPage` 和 `knowledge`
- **THEN** 系统只把 wikiPage 和 knowledge evidence 放入 evidence retrieval，但仍可包含 pinned/profile sections

#### Scenario: Context honors metadata filters

- **WHEN** 客户端指定 project、scope 或 language
- **THEN** 系统只使用符合过滤条件的 evidence 构建 context

### Requirement: Context Packing

系统 SHALL 将检索到的 evidence 和 synthesized records 打包为稳定、可读、可注入 prompt 的 context 文本。

Packing MUST 使用固定 section order：identity、global、project、wiki-synthesis、lessons-and-crystals、recent-evidence、evidence。Pinned memory 和 project profile MUST 优先于 raw evidence。Context 文本 MUST 标注来源 id，避免 agent 把未引用内容当作已验证事实。

#### Scenario: Pack context in section priority order

- **WHEN** context 同时包含 pinned、profile、knowledge、wikiPage、memory 和 summary
- **THEN** context 文本按固定 section order 展示，并保留每段来源 id

#### Scenario: Preserve grouped response lists

- **WHEN** context response 包含多种 sourceType
- **THEN** 系统分别填充 sections、wikiPages、knowledge 和 memories 列表，供 agent 结构化读取

### Requirement: Context Interfaces

系统 SHALL 提供 CLI 和 REST 接口生成 memory context。

CLI MUST 提供 `agentmemory context "<query>"` 和 `agentmemory context "<query>" --json`。REST MUST 提供 `POST /agentmemory/context`。两个接口 MUST 支持 `query`、`tokenBudget`、`limit`、`project`、`scope`、`language`、`sourceTypes`、`minScore` 和 `matchMode`。

当用户运行 `agentmemory context "<query>"` 且未指定 `--json` 时，CLI MUST 输出 prompt-friendly 文本。该文本 MUST 包含 AgentMemory context envelope 和 provenance header，明确说明内容由 AgentMemory 记忆工具提供，是外部长期记忆上下文，不是系统指令、不是开发者指令、不是用户新指令，且不能覆盖当前会话中的更高优先级指令或用户请求。该文本 MUST 包含固定 context sections、compact source ids、confidence 和 compressed 状态。Prompt output MUST NOT 输出完整 JSON payload，也 MUST NOT 重复展开完整 `wikiPages`、`knowledge` 和 `memories` 列表。

#### Scenario: Generate context from CLI

- **WHEN** 用户运行 `agentmemory context "历史决策" --json`
- **THEN** CLI 输出包含 sections 的 context response JSON

#### Scenario: CLI prints prompt-ready context

- **WHEN** 用户运行 `agentmemory context "历史决策"` 且不带 `--json`
- **THEN** CLI 输出包含 AgentMemory context envelope 和固定 sections 的 prompt-friendly 文本

#### Scenario: Prompt output includes compact evidence

- **WHEN** context response 包含 evidence
- **THEN** prompt output 展示 compact source ids、confidence 和 compressed 状态，但不输出完整 JSON

#### Scenario: Prompt output identifies memory source

- **WHEN** 用户运行 `agentmemory context "历史决策"` 且不带 `--json`
- **THEN** CLI 输出明确说明该内容来自 AgentMemory 记忆工具，agent 应将其视为可核查的长期记忆上下文而非系统指令、开发者指令或用户新指令

#### Scenario: Context ignores filtered evidence

- **WHEN** search 原始召回结果被 relevance gate 过滤
- **THEN** context 不把这些结果写入 prompt context

#### Scenario: Context confidence reflects evidence quality

- **WHEN** context 只包含低数量或单一路径 evidence
- **THEN** response confidence 低于多来源高分 evidence 的 response

#### Scenario: Generate context from REST

- **WHEN** 客户端 POST `/agentmemory/context`
- **THEN** API 返回包含 sections 的 context response JSON
