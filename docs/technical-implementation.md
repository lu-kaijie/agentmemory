# AgentMemory 技术实现说明

本文说明 AgentMemory 的技术实现、模块拆分、关键设计取舍，以及 RAG 和 LLM Wiki 的内部工作方式。面向维护者、二次开发者和需要理解系统边界的 agent。

## 总体架构

AgentMemory 采用 Python + FastAPI + Typer 的本地服务架构，核心原则是“状态中心化、入口轻量化、派生任务异步化”。

主要模块：

- `src/agentmemory/config.py`：读取环境变量，管理默认值，输出脱敏配置摘要。
- `src/agentmemory/api/app.py`：FastAPI 装配入口，提供 REST、Viewer 和后台 maintenance worker。
- `src/agentmemory/cli.py`：Typer CLI，供用户和 shell-capable agent 调用。
- `src/agentmemory/core/models.py`：Pydantic 数据模型，定义请求、响应和状态记录。
- `src/agentmemory/core/service.py`：核心业务服务，处理 observation、memory、session、Wiki、governance 和 maintenance。
- `src/agentmemory/core/search.py`：搜索与索引服务，负责 FTS5、LanceDB、hybrid search 和 context packing。
- `src/agentmemory/providers/`：OpenAI-compatible LLM 和 embedding provider。
- `src/agentmemory/state/`：SQLite `StateKV`，提供统一 KV scope 和 FTS5 操作。
- `src/agentmemory/viewer/`：内置 Viewer 静态页面。
- `skills/agentmemory/SKILL.md`：agent 使用说明。

REST 和 CLI 不直接读写 SQLite；它们只把输入转换成 Pydantic request，再调用 core service。这样能避免 CLI、REST、Viewer 行为漂移。

## 技术选型概览

核心技术选型是 Python、FastAPI、Typer、Pydantic v2、SQLite、FTS5、LanceDB 和 OpenAI-compatible providers。整体目标是让本地部署简单、状态可迁移、接口结构化，并且让 LLM/RAG 能力可以在 CLI、REST、Viewer 和 Skill 之间复用。

## 为什么选择 Python

AgentMemory 的核心工作是 LLM 调用、embedding、RAG、文本处理、本地向量库和后台任务。Python 在这些方向生态成熟，适合快速迭代和本地部署：

- OpenAI SDK 和兼容生态完整。
- LanceDB、SQLite、Pydantic、FastAPI 集成成本低。
- pytest 和 TestClient 能覆盖 service、CLI、REST 的完整路径。
- 后续做 eval、benchmark、文本处理和多模态能力更方便。

## 为什么选择 FastAPI

FastAPI 用于 REST API 和 Viewer 托管。

选择理由：

- Pydantic v2 能直接复用 core models。
- OpenAPI、请求校验、错误响应和 TestClient 都是现成能力。
- 适合本地服务和后续服务化部署。
- lifespan 能自然承载后台 maintenance worker。

REST 默认保持裸 JSON，避免破坏 CLI、Viewer 和现有调用方；需要统一响应时，通过 `?envelope=true` 或 `AGENTMEMORY_REST_ENVELOPE=true` 返回：

```json
{
  "status_code": 200,
  "body": {},
  "headers": {}
}
```

## 为什么选择 Typer CLI

AgentMemory 的首要使用者是 coding agent。很多 agent 可以稳定调用 shell 命令，因此 CLI 是最可靠的接入面。

Typer 的优势：

- 参数声明清晰，适合 agent 生成命令。
- `--json` 可输出结构化结果，便于程序解析。
- 默认文本输出适合人类验收。
- 和 Pydantic/FastAPI 的类型风格一致。

常见命令分组：

- `agentmemory observe`
- `agentmemory remember`
- `agentmemory session start/end`
- `agentmemory search`
- `agentmemory smart-search`
- `agentmemory context`
- `agentmemory wiki ...`
- `agentmemory index ...`
- `agentmemory maintenance run`
- `agentmemory export/import/forget`

## 状态层：为什么用 SQLite 和 StateKV

AgentMemory 第一版定位为本地长期记忆。SQLite 的优点是：

- 单文件持久化，部署简单。
- 易备份、易导出、易迁移。
- 支持事务和 FTS5。
- 本地运行不需要额外数据库服务。

业务层不直接操作 SQL 表，而是通过 `StateKV` 按 scope 保存 JSON-like records：

- `sessions`
- `observations`
- `memories`
- `summaries`
- `memoryCandidates`
- `llmProcessingJobs`
- `knowledge`
- `wikiPages`
- `wikiUpdateJobs`
- `indexJobs`
- `audit`

这样做的原因：

- 早期 schema 变化更灵活。
- 导入导出可以直接复用 Pydantic model。
- 后续迁移到 SQL 表、远程 KV 或服务端存储时，core service 不需要大改。
- audit、search document 和业务记录可以保持清晰边界。

## Scope 和 Project Identity

长期记忆分为两层：

- `scope=global`：跨项目生效的偏好、规则、lesson、insight。
- `scope=project`：只属于某个项目的 observation、summary、project memory、Wiki page、knowledge、profile 和 pinned memory。

Project 是一等实体 `ProjectRecord`，包含 `id`、`name`、`root`、`aliases`、`metadata`、`createdAt` 和 `updatedAt`。

默认识别方式：

1. 使用请求传入的 `cwd`，没有则使用进程当前目录。
2. 对 `cwd` 做 `realpath`，得到稳定 root。
3. `name = basename(root)`，除非请求显式传入 project。
4. `id = sha256(root)[:24]` 加 `proj_` 前缀，避免同名目录冲突。

系统不依赖项目目录里的状态文件。这样即使 agent 被直接关闭，也不会因为文件状态未更新导致 session 失真。Session 只作为内部 evidence 容器；`observe` 没有传 `sessionId` 时，会按 project current active session + TTL 尽力归组，过期则创建新 session。

## Provider 设计

LLM 和 embedding 都采用 OpenAI-compatible provider。

LLM provider 负责：

- observation summary
- candidate memory extraction
- search explanation
- context compression
- Wiki update proposal
- knowledge distillation
- session summary

Embedding provider 负责：

- 把 searchable text 转为向量。
- 支持 observation、summary、memory、knowledge、wikiPage 的语义检索。

为什么不把 LLM 和 embedding 混成一个 provider：

- 成本模型不同。
- 延迟和调用频率不同。
- 用户可能选择不同供应商或不同模型。
- embedding failure 不应阻塞关键词搜索。

## 写入链路

### Observation

`agentmemory observe` 的流程：

1. 保存 observation。
2. 更新或创建 session。
3. 调用 LLM 生成 summary。
4. 调用 LLM 提炼 candidate memories。
5. 保存 summary、candidate memories 和 LLM processing job。
6. 为 observation/summary 创建 search document 和 embedding job。
7. 创建 Wiki update job。
8. 写 audit。

如果 LLM 失败：

- observation 仍保留。
- LLM processing job 标记为 `failed`。
- `maintenance run` 可以后续重试。

### Remember

`agentmemory remember` 的流程：

1. 保存用户显式 memory。
2. 写 audit。
3. 写入 FTS5 search document。
4. 创建 embedding update job。
5. 创建 Wiki update job。

这类 memory 是用户明确要求长期保存的内容，不需要先进入 candidate 状态。

### Session

`session start` 保存会话元数据。

`session end` 会：

1. 汇总该 session 的 observations。
2. 调用 LLM 生成 session summary。
3. 保存 summary。
4. 更新 session status、endedAt、summaryId。
5. 为 summary 创建 search document 和 Wiki update job。

## RAG 实现

AgentMemory 的 RAG 是“记忆证据 RAG”，不是代码仓库全文 RAG。

### 索引对象

可以进入搜索索引的对象：

- observation
- memory
- summary
- knowledge
- wikiPage

每个对象都会转换为 `SearchDocument`：

- `id`
- `sourceType`
- `sourceId`
- `sessionId`
- `content`
- `searchableText`
- `language`
- `scope`
- `project`
- `projectId`
- `files`
- `concepts`
- `createdAt`

### FTS5 关键词索引

写入 memory/observation/summary/wikiPage/knowledge 时，系统同步写入 SQLite FTS5。

这样做的原因：

- 关键词搜索可以立即可用。
- 即使 embedding provider 失败，也能通过精确词搜索找到证据。
- 文件名、函数名、命令、错误码、概念词更适合关键词召回。

### LanceDB 向量索引

向量写入不阻塞业务写入。

系统会创建 `embedding_update` index job，后台 worker 或 `maintenance run` 再调用 embedding provider，把向量写入 LanceDB。

这样做的原因：

- embedding 调用可能慢或失败。
- 保存记忆不应该因为向量服务暂时不可用而失败。
- pending/failed job 可被重试，数据不会丢。

### Hybrid Search

`mode=hybrid` 会合并 keyword 和 vector 结果：

1. FTS5 召回关键词结果。
2. LanceDB 召回语义结果。
3. 根据 `sourceId` 去重。
4. 对同时命中 keyword 和 vector 的结果加权。
5. 应用 `sourceTypes`、`scope`、`project`、`projectId`、`sessionId`、`language`、`minScore` 等过滤。
6. 返回带 `matchSources` 的结构化结果。

`matchSources` 用于告诉 agent：结果来自关键词、向量，还是两者都有。

### Relevance Gate

为了减少弱相关召回，搜索支持：

- `matchMode=auto`：默认模式，对短查询更谨慎。
- `matchMode=any`：宽召回，适合验收或探索。
- `matchMode=all`：要求 query terms 都命中。
- `matchMode=phrase`：短语匹配。
- `minScore`：过滤低分结果。

`smart-search` 和 `context` 默认只使用通过 gate 的结果，避免把噪声注入 prompt。

## Context 构建

`agentmemory context "<query>"` 面向 agent prompt 注入。

默认 context 是 project scope：检索时包含 global records 和当前 project records。默认 source types 偏向稳定知识：

- wikiPage
- knowledge
- memory
- summary
- observation

context 输出分两种：

- 默认文本：带 `<agentmemory-context>` 包裹，并固定输出 sections，可直接放入 prompt。
- `--json`：返回 `context`、`sections`、`project`、`evidence`、`wikiPages`、`knowledge`、`memories`、`confidence`、`compressed`。

固定 sections：

- `identity`
- `global`
- `project`
- `wiki-synthesis`
- `lessons-and-crystals`
- `recent-evidence`
- `evidence`

Pinned memory 和 project profile 优先进入 `global` / `project` section。Wiki synthesis、lesson、crystal、insight 进入稳定知识 section。原始 evidence 保留 source ids、score 和 matchSources，便于 agent 核查。

当内容超过 token budget：

- 如果 LLM 可用，调用 LLM 压缩 context。
- 如果 LLM 不可用，做截断。

context 明确声明：

- 它是外部长期记忆证据。
- 不是系统指令。
- 不是开发者指令。
- 不是用户新指令。
- 不能覆盖当前用户要求。

这是为了避免 agent 把历史记忆误解为当前任务指令。

## LLM Wiki 实现

LLM Wiki 是 RAG 之上的稳定知识层。

RAG 负责找到 evidence；LLM Wiki 负责把 evidence 沉淀成可复用知识。

### 为什么需要 LLM Wiki

如果只有 RAG，每次新任务都需要从 observation、summary、memory 中重新归纳：

- 哪些事实稳定？
- 哪些流程已经形成习惯？
- 哪些错误已经修过？
- 哪些技术决策已经确认？

LLM Wiki 把这些归纳结果持久化，减少重复总结和上下文噪声。

### Knowledge Distillation

Wiki update 前，系统先把 evidence 提炼为 knowledge：

- `semantic`：事实和稳定结论。
- `procedural`：流程、操作方式、工作习惯。
- `lesson`：经验教训，支持 reinforcement。
- `crystal`：阶段性摘要，按 source group 去重。

每条 knowledge 保存：

- `kind`
- `content`
- `sourceIds`
- `concepts`
- `files`
- `confidence`
- `fingerprint`
- `reinforcements`
- `lastReinforcedAt`
- `sourceGroup`

### 去重与强化

knowledge 写入前会生成 fingerprint。

策略：

- 精确重复：复用已有 record，合并 sourceIds。
- lesson 重复：增加 `reinforcements`，更新 `lastReinforcedAt`，提高 confidence。
- crystal：同一 source group 复用稳定记录，避免 rebuild 时重复生成近似摘要。

这样能避免 Wiki rebuild 或多 topic update 带来大量重复 knowledge。

### Consolidation 和生命周期

LLM Wiki 不只在单条 evidence 写入时更新页面，还会周期性对 summaries、memories 和已有 knowledge 做 consolidation。Consolidation 要求 LLM provider：系统会让 LLM 读取 evidence、已有 knowledge、insights 和 Wiki pages，再输出结构化 knowledge、动态页面和 lint issues。LLM 不可用时返回明确错误，不用关键词规则伪造 consolidation。

- 多条 evidence 支撑同一结论时，沉淀或强化 semantic knowledge。
- 重复出现的流程会沉淀或强化 procedural knowledge。
- lesson 支持 recall、strengthen、decay 和 soft delete。
- crystal 使用 source group 作为稳定边界，避免重复生成同一组 evidence 的阶段性摘要。
- reflect 会从 semantic、procedural、lesson、crystal 中归纳 insight。
- query filing 可以把高价值问答沉淀为 insight、knowledge 或 crystal。
- LLM consolidation 可以判断 stable facts、merge candidates、contradiction 和 stale claims。

这些机制让知识层持续复利，而不是每次查询都从 raw evidence 重新归纳。

### Wiki Page 聚合

当前版本保留固定 topic 作为导航和可读聚合入口：

- personal_preferences
- project_overview
- technical_decisions
- troubleshooting
- files_and_modules
- workflow_habits

固定 topic 的原因：

- 早期减少自由生成页面导致的碎片化。
- agent 更容易知道去哪里找稳定知识。
- Viewer 展示更简单。
- context packing 可以优先使用稳定入口。

固定 topic 不是 LLM Wiki 的本质。系统还支持动态 Wiki page：`entity`、`concept`、`source`、`comparison`、`synthesis`。动态页由 LLM consolidation 创建，使用 `type + slug` 复用更新，并带有 parent topic 方便导航。动态页会进入 search/context，title、type、slug、parent topic 和 content 都可检索。

`wiki lint` 同样要求 LLM 判断 contradiction/stale，再追加 deterministic checks：

- knowledge 缺少 sourceIds：missing_source。
- knowledge confidence 过低：low_confidence。
- Wiki page 缺少 sourceIds：orphan。

Wiki update job 包含：

- `sourceIds`
- `topic`
- `status`
- `proposal`
- `attempts`
- `lastError`
- `createdAt`
- `updatedAt`

处理流程：

1. observation、memory、summary 写入后创建 `wiki_update_job`。
2. maintenance 或 `wiki update` 读取 pending jobs。
3. 收集 sourceIds 对应 evidence 和已有 Wiki 页面。
4. 调用 LLM 生成结构化 proposal。
5. 校验 proposal。
6. 应用到 Wiki 页面。
7. 为 Wiki 页面创建 search document 和 embedding job。
8. 写 audit。

### 为什么 Wiki 不直接等于 RAG

RAG 是召回层，回答“哪些证据相关”。

LLM Wiki 是沉淀层，回答“这些证据长期意味着什么”。

两者配合方式：

- observation/memory/summary 进入 RAG。
- RAG evidence 进入 knowledge distillation。
- knowledge 聚合成 Wiki 页面。
- Wiki 页面和 knowledge 再进入 RAG。
- context 优先使用更稳定的 Wiki/knowledge，再补充原始 memory。

这形成一个闭环：记录、检索、沉淀、再检索。

## Maintenance 和失败恢复

AgentMemory 不要求外部队列或独立 cron。第一版使用轻量进程内 maintenance worker，并提供 CLI/REST 手动入口。

配置：

- `AGENTMEMORY_MAINTENANCE_ENABLED`
- `AGENTMEMORY_MAINTENANCE_INTERVAL_SECONDS`
- `AGENTMEMORY_MAINTENANCE_LIMIT`

手动入口：

```bash
uv run agentmemory maintenance run --json
```

REST：

```http
POST /agentmemory/maintenance/run
```

maintenance 会处理：

- index repair
- pending/failed embedding jobs
- failed LLM processing jobs
- pending/failed Wiki update jobs
- pending Wiki job 合并
- 页面压缩结果字段预留

为什么这么做：

- 写入路径保持快速。
- LLM/embedding 临时失败不会丢源数据。
- CLI、REST、后台 worker 使用同一套 service 方法。
- 后续可替换为外部队列，但不影响现有业务模型。

## Governance：导出、导入、删除和审计

AgentMemory 的长期记忆必须可治理。

### Export

`agentmemory export --json` 导出：

- schemaVersion
- sessions
- observations
- memories
- summaries
- memoryCandidates
- llmProcessingJobs
- knowledge
- wikiPages
- wikiUpdateJobs
- indexJobs
- audit

导出会写 audit，但不会泄露 API key 或 secret。

### Import

`agentmemory import --file <path> --json` 支持按 id 保守去重：

- 已存在 id 跳过。
- 不支持的 schemaVersion 拒绝。
- 导入后重建搜索索引入口。
- 导入动作写 audit。

### Forget

`agentmemory forget --memory-id <id>` 删除显式 memory：

- 删除 memory record。
- 删除对应 search document 和 index job。
- 写 audit。

第一版 forget 针对用户显式 memory，不直接级联删除 observation、summary、Wiki 和 knowledge。

## 配置说明

核心配置：

```bash
AGENTMEMORY_HOST=127.0.0.1
AGENTMEMORY_PORT=3111
AGENTMEMORY_DB_PATH=.agentmemory/agentmemory.sqlite3
AGENTMEMORY_VECTOR_DB_PATH=.agentmemory/vector
AGENTMEMORY_VECTOR_TABLE=memory_vectors

AGENTMEMORY_LLM_BASE_URL=https://api.openai.com/v1
AGENTMEMORY_LLM_API_KEY=
AGENTMEMORY_LLM_MODEL=

AGENTMEMORY_EMBEDDING_BASE_URL=https://api.openai.com/v1
AGENTMEMORY_EMBEDDING_API_KEY=
AGENTMEMORY_EMBEDDING_MODEL=

AGENTMEMORY_MAINTENANCE_ENABLED=true
AGENTMEMORY_MAINTENANCE_INTERVAL_SECONDS=10
AGENTMEMORY_MAINTENANCE_LIMIT=25
AGENTMEMORY_REST_ENVELOPE=false
```

`Settings.safe_summary()` 会隐藏敏感值，只展示是否已配置。

## 测试策略

测试覆盖：

- config
- StateKV
- OpenAI-compatible providers
- memory core service
- search service
- REST API
- CLI
- Wiki processing
- project docs

运行：

```bash
uv run pytest
uv run openspec validate --all --strict
```

## 后续扩展方向

当前架构给后续能力预留了位置：

- Hook adapter：自动采集轻量事件。
- MCP adapter：让不方便调用 shell 的 agent 使用工具接口。
- graph persistence：从 Viewer 派生图升级为持久化 knowledge graph。
- rerank：在 hybrid search 后加入 reranker。
- page compression：对过长 Wiki 页面做结构化压缩。
- retention/decay：低 confidence 或长期不用的 memory 衰减。
- advanced import compatibility：支持更多 schema 版本迁移。
