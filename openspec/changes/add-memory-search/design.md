## Context

系统目前已经具备真实 LLM/embedding provider、StateKV、memory core、LLM processing 和 CLI/REST 查询派生数据的能力。`observe` 可以保存 observation 并生成 summary/candidate memories，`remember` 可以保存用户明确长期记忆。

缺口是检索：agent 现在能写入记忆，但不能可靠地从历史 observation、summary 和 memory 中召回证据。根据产品文档，第一版 RAG 需要以 agent 工作过程为证据库，提供关键词召回、语义召回、混合检索和基于证据的 LLM explanation。

## Goals / Non-Goals

**Goals:**

- 为 observation、memory 和 summary 生成 searchable document。
- 使用 SQLite FTS5 实现关键词检索。
- 使用 embedding provider + LanceDB 实现本地向量检索。
- 在 `observe`、summary 生成和 `remember` 写入后更新索引。
- 保存 index job 状态，记录 embedding/index 失败。
- 提供 `search`、`smart-search`、index status、rebuild 和 repair 的 REST/CLI 入口。
- `smart-search` 合并关键词和向量结果，并用 LLM 基于 evidence/source ids 生成解释。
- embedding 或 LanceDB 更新失败时不丢失原始 observation/memory/summary。

**Non-Goals:**

- 不实现 Wiki 页面维护或 Wiki 索引。
- 不实现 Viewer 搜索页面。
- 不实现 MCP、Hook 或后台高频采集。
- 不实现 candidate memory 自动接受。
- 不实现跨语言重复治理、rerank 模型、图谱权重融合或 query translation。
- 不实现复杂后台 worker；第一版可以同步尝试索引并记录失败，repair/rebuild 作为手动补偿。

## Decisions

### 1. Searchable document 作为统一索引输入

所有可检索对象先转换成 `SearchDocument`：

- `id`
- `sourceType`: `observation`、`memory`、`summary`
- `sourceId`
- `sessionId`
- `content`
- `searchableText`
- `language`
- `project`
- `files`
- `concepts`
- `createdAt`

这样 FTS5 和 LanceDB 共享同一套 metadata，搜索结果可以稳定返回 source ids。`searchableText` 第一版由 title/content/files/concepts 拼接而成，不做自动翻译。

### 2. FTS5 同步写入，embedding 同步尝试但失败软降级

写入链路中，系统保存原始记录后：

1. 生成 `SearchDocument`。
2. 写入 SQLite FTS5。
3. 创建或更新 index job。
4. 调用 embedding provider 生成向量。
5. 写入 LanceDB。
6. job 标记为 `done` 或 `failed`。

FTS5 是本地 SQLite 能力，预期快速且可靠，因此写入时同步执行。embedding 和 LanceDB 可能受网络、模型、维度或本地文件影响，失败时不得回滚原始业务数据，必须记录 job `failed` 和 `lastError`，后续 repair/rebuild 可补偿。

### 3. LanceDB 作为第一版向量库

第一版使用 LanceDB 本地嵌入式向量库，而不是在 SQLite 中手写向量比对。

理由：

- 不需要独立服务，符合个人本地部署。
- 支持 metadata 和向量检索，后续迁移成本较低。
- 避免 SQLite 手写向量逐条扫描带来的实现和性能问题。

配置新增：

- `AGENTMEMORY_VECTOR_DB_PATH`
- `AGENTMEMORY_VECTOR_TABLE`

默认路径可放在 `~/.agentmemory/vector`。

### 4. `search` 与 `smart-search` 分层

`search` 是确定性检索入口：

- 默认使用 FTS5 关键词检索。
- 可选支持 `mode=keyword|vector|hybrid`。
- 返回 ranked results、source ids、score 和 metadata。
- 不调用 LLM。

`smart-search` 是 agent 友好的 RAG 入口：

- 执行 hybrid 检索。
- 合并 FTS5 与 vector 结果。
- 按来源去重。
- 使用简单归一化分数合并排序。
- 调用 LLM `explain_search(query, results)` 生成解释。
- 返回 `answer`、`results`、`evidence` 和 `context`。

第一版不实现复杂 rerank。LLM explanation 只能基于传入 results，不允许无证据扩写。

### 5. Index rebuild/repair 手动触发

第一版不实现常驻后台 worker。提供：

- `index status`：查看索引文档数、job 状态、失败数、provider 状态。
- `index rebuild`：清空并重建 FTS5/LanceDB。
- `index repair`：只补建缺失或 failed 的 index jobs。

实现时可以先以同步命令完成，后续后台任务 change 再把 repair/rebuild worker 化。

### 6. 多语言策略

中文、英文和中英混合都保存原文。FTS5 负责精确词、文件名、函数名、命令和错误码；LanceDB 负责自然语言语义匹配。

第一版可以增加轻量 `search_terms`：

- 原始 content。
- files/concepts。
- 对中文文本生成简单字符 n-gram 或保留连续中文片段。

不做自动翻译，避免成本、延迟和语义噪声。

## Risks / Trade-offs

- LanceDB 依赖可能增加安装复杂度 -> 明确依赖并通过 doctor/index status 检查本地路径可用性。
- embedding 失败导致语义检索缺失 -> FTS5 仍可用，job 记录失败，repair 可补偿。
- 同步 embedding 增加 `observe`/`remember` 延迟 -> 第一版优先可验收；后续后台 worker 优化。
- FTS5 中文分词有限 -> 通过 embedding 覆盖中文语义检索，并可加简单 search_terms。
- LLM explanation 可能幻觉 -> 所有 smart-search 响应必须返回 evidence/source ids，prompt 限制只基于 results。
- Rebuild 可能重复索引或维度不一致 -> rebuild 先清空索引，repair 检查 embedding model 和 vector dimension。

## Migration Plan

1. 增加 FTS5 schema、index job scope 和 LanceDB 配置。
2. 新增 SearchDocument、SearchResult、SearchResponse、SmartSearchResponse、IndexJob、IndexStatus 模型。
3. 实现 index service：document builder、FTS5 writer/searcher、LanceDB writer/searcher、job 状态。
4. 集成 memory core 写入链路。
5. 增加 REST/CLI。
6. 增加 tests 和真实 provider smoke 测试。

已有历史数据不自动静默补建。用户可以执行 `agentmemory index rebuild` 或 REST rebuild 来为历史 observation/memory/summary 建索引。
