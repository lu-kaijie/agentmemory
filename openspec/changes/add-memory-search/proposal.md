## Why

系统已经能保存 observation、memory、summary 和 candidate memories，但 agent 还不能基于这些数据恢复上下文。下一步需要把已保存的个人记忆变成可检索证据库，让 agent 可以通过关键词、语义和混合检索找到过去的决策、结论和工作过程。

本变更实现第一版 RAG/search 能力：为可检索文本建立关键词索引和向量索引，提供 `search` 与 `smart-search`，并让 LLM 基于召回证据生成可解释结果。

## What Changes

- 新增 memory search 能力：
  - 为 observation、memory 和 summary 生成 searchable document。
  - 使用 SQLite FTS5 建立关键词索引。
  - 使用 embedding provider 生成向量并写入本地 LanceDB。
  - 支持关键词检索、语义检索和混合检索。
  - `smart-search` 合并 FTS5 与向量结果，去重、排序，并保留 source ids。
  - LLM 基于检索结果生成简短解释，结果必须包含 evidence/source ids。
- 扩展写入流程：
  - `observe` 保存 observation 后为 observation 建索引。
  - LLM processing 成功生成 summary 后为 summary 建索引。
  - `remember` 保存 memory 后为 memory 建索引。
  - embedding 写入失败不得导致原始数据写入失败，但必须记录 index job 状态和错误。
- 增加索引状态和修复能力：
  - 保存 index jobs。
  - 提供 index status。
  - 提供手动 rebuild/repair 的 CLI 和 REST 入口。
- 扩展 REST/CLI：
  - `POST /agentmemory/search`
  - `POST /agentmemory/smart-search`
  - `GET /agentmemory/index/status`
  - `POST /agentmemory/index/rebuild`
  - `POST /agentmemory/index/repair`
  - `agentmemory search`
  - `agentmemory smart-search`
  - `agentmemory index status`
  - `agentmemory index rebuild`
  - `agentmemory index repair`
- 不实现 Wiki 页面维护、Viewer、Hook、MCP、自动接受 candidate memories 或跨语言重复治理。

## Capabilities

### New Capabilities

- `memory-search`: observation、memory、summary 的关键词检索、向量检索、混合检索、证据返回和 LLM 解释能力。
- `memory-indexing`: searchable document、FTS5、LanceDB、embedding index jobs、index status、rebuild 和 repair 能力。

### Modified Capabilities

- `memory-core`: `observe`、`remember` 和 summary 生成后需要触发索引写入或索引任务记录。
- `memory-core-interfaces`: REST 和 CLI 增加 search、smart-search 和 index 管理入口。
- `llm-provider`: search explanation 使用现有 LLM provider 边界，要求解释必须基于 evidence/source ids。

## Impact

- 新增本地索引模块、search service 和 index job 模型。
- 增加 LanceDB 依赖和本地索引目录配置。
- 扩展 SQLite schema 以支持 FTS5 和 index job 状态。
- 修改 memory core service 写入链路以触发索引更新。
- 修改 REST app 和 CLI 增加搜索与索引管理命令。
- 增加 FTS5、embedding、LanceDB、混合排序、LLM explanation、失败降级和 rebuild/repair 测试。
