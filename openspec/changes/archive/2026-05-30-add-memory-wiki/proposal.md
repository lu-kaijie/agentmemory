## Why

AgentMemory 已经能保存、检索和治理记忆，但还缺少把高频 evidence 沉淀成稳定知识的 LLM Wiki 能力。这里的 LLM Wiki 不是单纯的页面功能，而是长期知识沉淀思想：把 observation、memory、summary 和检索 evidence 持续提炼为可读、可引用、可演化、可检索的知识层。

本变更先补齐 P0 的 Wiki 页面维护和 Wiki update job，把它作为长期知识层的第一阶段入口。固定 topic 页面用于给 agent 和用户提供可读聚合视图，后续 change 再扩展 semantic facts、procedural patterns、lessons、crystals 和 reflect insights。

## What Changes

- 新增 Wiki 页面数据模型：
  - `id`
  - `title`
  - `topic`
  - `content`
  - `sourceIds`
  - `confidence`
  - `createdAt`
  - `updatedAt`
- 新增 Wiki update job：
  - 从 observation、memory、summary 入队
  - 记录 pending/running/applied/failed 状态
  - 保存 proposal、attempts、lastError 和时间戳
- 新增 distilled knowledge 记录：
  - `semantic`：稳定事实
  - `procedural`：流程和习惯
  - `lesson`：经验教训
  - `crystal`：阶段性工作结晶摘要
  - 保存 sourceIds、concepts、files、confidence 和时间戳
- 新增 LLM Wiki 处理：
  - 基于 evidence 先提炼 distilled knowledge
  - 基于 evidence、distilled knowledge 和现有 Wiki 页面生成 update proposal
  - 应用 proposal 创建或更新 Wiki 页面
  - distilled knowledge 和 Wiki 页面更新后写 audit 并触发搜索索引
- 明确第一版 Wiki 页面的定位：
  - Wiki 页面是 LLM Wiki 思想的 P0 聚合视图，不是最终完整形态
  - 后续应从 distilled knowledge 聚合 Wiki，而不是只从单条 evidence 直接改写页面
  - 后续知识层包括 semantic facts、procedural patterns、lessons、crystals 和 reflect insights
- 新增 REST API：
  - `GET /agentmemory/wiki/pages`
  - `GET /agentmemory/wiki/jobs`
  - `POST /agentmemory/wiki/update`
  - `POST /agentmemory/wiki/rebuild`
- 新增 CLI：
  - `agentmemory wiki pages`
  - `agentmemory wiki jobs`
  - `agentmemory wiki update`
  - `agentmemory wiki rebuild --topic <topic>`
  - `agentmemory wiki rebuild --all`
- 扩展 search index，使 Wiki 页面可被 keyword/vector/hybrid search 检索。
- 扩展 Web Viewer，只读展示 Wiki 页面和 Wiki jobs。
- 本变更不实现 MCP、Hook、知识图谱抽取、Wiki 手动编辑、权限系统、导入、复杂冲突合并或 reflect insights。

## Capabilities

### New Capabilities

- `memory-wiki`: LLM Wiki 页面、Wiki update job、更新/重建流程和审计能力。

### Modified Capabilities

- `memory-core`: 增加 Wiki 页面和 Wiki update job 的列表能力。
- `memory-core-interfaces`: 增加 Wiki REST 和 CLI 接口要求。
- `memory-indexing`: 增加 Wiki 页面索引要求。
- `memory-search`: 增加 Wiki 页面作为可搜索 source type 的要求。
- `web-viewer`: 增加只读 Wiki 页面和 Wiki job 展示要求。

## Impact

- Core models：新增 `WikiPageRecord`、`WikiUpdateJobRecord`、Wiki 相关 request/response。
- Core models：新增 `KnowledgeRecord`，用于 semantic/procedural/lesson/crystal。
- StateKV scopes：新增 `KV.knowledge`、`KV.wikiPages` 和 `KV.wikiUpdateJobs`。
- LLM provider：需要 knowledge distillation 和 Wiki update proposal 生成能力，可复用现有 OpenAI-compatible chat completions。
- Core service：observe/remember/summary 后创建 Wiki update job；处理 job 时先提炼 knowledge，再更新 Wiki；新增 update/rebuild/list wiki/knowledge 能力。
- Search/index：distilled knowledge 和 Wiki 页面写入 searchable document、FTS5 和 LanceDB。
- REST/CLI/Viewer：新增 Wiki 查询、knowledge 查询、更新和重建入口。
- Tests：新增 Wiki service、REST、CLI、search indexing 和 Viewer 测试。
