# AgentMemory 产品文档

## 1. 产品定位

AgentMemory 是一个 AI native 的长期记忆平台，面向 AI coding agent、开发者和多 agent 协作流程。它不是普通笔记系统，也不是传统 CRUD 服务外加 AI 功能，而是以 agent 工作流为核心设计的记忆基础设施。

产品目标是让 agent 在跨会话、跨任务和跨工具执行过程中保留上下文、复用历史经验、追踪决策依据，并通过 Skill、CLI 和 REST API 被不同 agent 稳定调用。

核心原则：

- Agent-first：agent 是首要用户，接口必须适合工具调用、结构化返回和上下文注入。
- LLM-first：LLM 从第一版参与摘要、记忆提炼、搜索解释和上下文压缩。
- LLM-required but low-frequency：系统必须配置真实 LLM/embedding provider，但 Skill 必须限制 LLM 调用频率，只在关键节点触发。
- Tool-callable：核心能力必须能被 CLI 和 REST API 调用。
- State-centered：所有边界入口共享同一套状态和内部能力，避免接口行为漂移。
- Governable：保存、删除、导出和导入必须可追踪、可审计。

## 2. 要解决的问题

AI coding agent 在真实开发中会反复执行探索、阅读、修改、测试和复盘，但单次会话结束后大量信息会丢失：

- 已经读过哪些文件、得出过哪些结论。
- 哪些技术决策已经确定，原因是什么。
- 哪些错误已经出现过，如何修复。
- 用户明确要求长期保留的偏好、规则或事实。
- 多个 agent 之间如何共享上下文和任务状态。

AgentMemory 要把这些过程信息变成可搜索、可压缩、可治理的长期记忆，使后续 agent 能快速恢复上下文，而不是重复探索。

## 3. 目标用户

### AI coding agent

通过项目 Skill 获得使用规则，通过 CLI 或 REST API 写入、搜索、压缩和注入上下文。

### 开发者

通过 REST API、Viewer 和导出文件查看 agent 记忆，显式保存或删除长期记忆，检查服务健康状态。

### 维护者

配置 LLM provider、认证、索引、后台任务和高级功能开关，审计数据变更并维护数据迁移。

## 4. 核心场景

### 场景一：agent 记录关键工作过程

agent 在完成探索、修改、测试或复盘后，按 Skill 说明调用 CLI 或 REST API，把任务过程、相关文件、结论和结果写入 observation。服务保存 observation，维护 session 统计，并触发 LLM 摘要和候选记忆提炼。

Skill 不应在每次文件读取、每次编辑、每次命令执行后都调用 `observe`。第一版 `observe` 会触发 LLM processing，因此应只在阶段性节点调用，例如完成一次探索、完成一个修改并验证结果、发现关键问题、用户纠正方向或任务阶段结束。

### 场景二：用户显式保存长期记忆

用户要求保存某个事实、偏好、决策或经验时，agent 调用 `agentmemory remember` 或 REST API。服务保存 memory，标注 type、concepts、files，并写入 audit。

### 场景三：后续会话恢复上下文

agent 启动新任务后按 Skill 说明调用 CLI 或 REST API，服务先做关键词/BM25 和 embedding 召回，再用 LLM 生成匹配说明和压缩上下文，返回适合 agent 注入 prompt 的内容。

### 场景四：治理和导出

用户可以导出完整数据，删除错误或过期记忆，并通过 audit trail 查看保存、删除、导入和导出的历史。

## 5. 产品范围

### P0：首版必须具备

- Python/FastAPI 服务骨架。
- OpenAI-compatible LLM provider 接口和首个真实 provider。
- OpenAI-compatible embedding provider 接口和首个真实 provider。
- 文件型 SQLite 状态层和 `StateKV` 抽象。
- `sessions`、`observations`、`memories`、`summaries`、`audit` 核心状态。
- `mem::observe`、`mem::remember`、`mem::search`、`mem::smart-search`、`mem::context`、`mem::wiki-update`。
- LLM 摘要、候选记忆提炼、搜索解释、上下文压缩和 Wiki 页面维护。
- CLI：`agentmemory remember`、`agentmemory observe`、`agentmemory search`、`agentmemory smart-search`、`agentmemory context`、`agentmemory wiki`、`agentmemory index`、`agentmemory export`、`agentmemory forget`、`agentmemory serve`。
- REST API：`/agentmemory/observe`、`/agentmemory/remember`、`/agentmemory/search`、`/agentmemory/smart-search`、`/agentmemory/context`、`/agentmemory/wiki/pages`、`/agentmemory/wiki/jobs`、`/agentmemory/wiki/knowledge`、`/agentmemory/wiki/update`、`/agentmemory/wiki/rebuild`、`/agentmemory/export`、`/agentmemory/forget`、`/agentmemory/health`。
- Skill：提供 agent 使用说明，指导优先调用 CLI，必要时直接调用 REST API。
- Web Viewer：支持搜索、memory 列表、Wiki 页面、health 和简单关系图。
- 导出、删除、审计和健康检查。

P0 验收标准：

- CLI 或 REST 能写入 observation。
- LLM 能为 observation 生成摘要、候选记忆或 Wiki 更新建议。
- CLI 或 REST 能搜索到 observation、summary、Wiki 页面和 memory。
- 用户显式 memory 能保存、导出、删除，并产生 audit。
- LLM 或 embedding provider 不可用时，服务不能进入可用运行状态。

候选记忆提炼使用 XML-like `<memory>` 标签格式解析 LLM 输出。普通 JSON prompt 输出和解释性文本不应被兜底保存为候选记忆，避免误存不符合结构的数据。

### P1：应具备

- session start/end 和会话级 summary。
- timeline、relations 和治理删除增强。
- Viewer 展示 sessions、memories、Wiki、关系图、health 和 provider 状态。
- import/export 版本兼容。
- 自动采集适配器和上下文注入开关。

### P2：高级能力

- MCP adapter 和 Hook adapter，作为后续可选生态集成。
- hybrid search：BM25、向量、图关系权重融合和 rerank。
- knowledge graph 和 temporal graph。
- 多模态 image refs 和 vision search。
- actions、leases、routines、signals、checkpoints 等多 agent 协作能力。
- eval、benchmark 和 self-correct。

## 6. 技术架构

推荐分层：

- `src/agentmemory/api/app.py`：服务装配入口，加载配置、初始化 provider、状态层、REST、Viewer 和后台任务。
- `src/agentmemory/config.py`：环境变量、默认值和配置校验。
- `src/agentmemory/providers/`：OpenAI-compatible LLM provider 和 embedding provider。
- `src/state/`：`StateKV`、KV scope、SQLite 持久化、索引和 audit 工具。
- `src/functions/`：内部业务能力，统一使用 `mem::*` 命名。
- `src/triggers/`：REST adapter，负责认证、校验、字段白名单和响应格式。
- `src/agentmemory/cli.py`：统一 CLI 入口，供 Skill 和 shell-capable agent 调用。
- `skills/`：项目 Skill，说明 agent 何时保存、搜索、更新 Wiki 和注入上下文。
- `src/adapters/`：后续可选 MCP、Hook 或编辑器集成适配器。
- `src/viewer/`：最小 Viewer 和健康页面。
- `test/`：单元测试、集成测试和端到端验收。

边界入口只做适配，不直接读写 SQLite。所有状态变更必须经过内部 `mem::*` 函数。

## 7. 技术选型

### 运行时和语言

- 语言：Python 3.11+。
- Web 运行时：Uvicorn。
- 包管理：uv。
- 类型和数据模型：Pydantic v2。

选择原因：Python 在 LLM、embedding、RAG、文本处理、后台任务和数据科学工具链上生态更完整；FastAPI + Pydantic 能很好地约束 REST、CLI 和内部函数的数据结构。

### 服务端

- HTTP 框架：FastAPI。
- 输入校验：Pydantic v2。
- 日志：structlog 或标准 logging，第一版优先使用标准 logging。
- 配置：pydantic-settings + `.env`。

选择原因：FastAPI 原生支持 OpenAPI、类型标注和 Pydantic schema，适合快速实现结构化 API；pydantic-settings 能统一管理模型、数据库、认证和功能开关配置。

### CLI

- CLI 框架：Typer。
- 输出格式：默认人类可读文本，`--json` 输出结构化 JSON。

选择原因：Typer 基于类型标注生成 CLI，和 FastAPI/Pydantic 的模型风格一致，适合第一版快速实现 `serve`、`observe`、`remember`、`search`、`smart-search`、`context`、`wiki`、`index`、`export`、`forget`、`doctor` 等命令。

### Web Viewer

- 前端框架：Vite + React。
- UI：普通 CSS Modules 或 Tailwind CSS 二选一，第一版优先使用 CSS Modules，减少设计系统复杂度。
- 图谱可视化：React Flow。
- 数据请求：fetch + 轻量 API client。

选择原因：Viewer 是产品第一版必需能力，但不需要复杂前端工程。React Flow 能快速实现节点、边、拖拽、缩放、点击详情和邻居展开，比手写 canvas 更适合第一版维护。

### 数据和索引

- 主存储：SQLite。
- SQLite 访问：SQLAlchemy 2.x + sqlite driver。
- 状态抽象：自研 `StateKV`，上层只访问 KV scope。
- 关键词搜索：SQLite FTS5。
- 向量索引：LanceDB，本地嵌入式向量库，用于保存 embedding 并执行语义检索。

选择原因：个人长期记忆第一版以本地可靠运行为主，SQLite 易部署、易备份、易导出，适合保存业务状态、审计和全文索引。LanceDB 不需要独立服务，能提供比 SQLite 手写向量比对更清晰的向量检索能力。`StateKV` 能隔离业务存储，后续迁移不会影响 CLI、REST 和 Viewer。

### RAG 实现

第一版 RAG 不是针对源代码文件做全文知识库，而是针对 agent 工作过程形成个人记忆证据库。

数据进入路径：

1. agent 通过 CLI 或 REST 写入 observation。
2. LLM 将 observation 压缩为 summary，并提炼 facts、decisions、files、concepts、lessons。
3. 系统把 observation、memory、summary、Wiki 页面写入 SQLite。
4. 系统为可检索文本写入 FTS5，并调用 embedding provider 生成向量。
5. 系统将向量和 metadata 写入 LanceDB。

检索路径：

1. `mem::search` 使用 FTS5 做关键词召回，适合文件名、函数名、错误信息和精确术语。
2. LanceDB embedding 检索做语义召回，适合自然语言问题和同义表达。
3. `mem::smart-search` 合并两路结果，去重、排序，并保留来源 id。
4. LLM 基于召回证据生成 `answer`、`evidence`、`wikiPages` 和可注入 `context`。

SQLite FTS5 是全文关键词检索，底层使用倒排索引和 BM25 排序，不计算 embedding，也不逐一比对向量。LanceDB 负责向量检索：系统把 query 转成 embedding，再在 LanceDB 中查找语义相近的记录。

第一版返回结构保留证据优先原则：LLM 可以总结，但必须返回支撑结论的 source ids。

#### 检索相关性待优化

当前第一版 memory search 以召回优先，FTS5 query 偏宽松，vector search 也暂未设置最低相关性阈值。因此在 query 包含 `memory`、`search`、`governance` 等泛词时，不太相关的 memory、observation 或 summary 也可能被召回。后续需要优化检索相关性：

- keyword search 支持更严格的 AND 模式或 phrase 模式。
- vector search 增加最低相关性阈值，过滤低置信结果。
- hybrid search 结合 sourceTypes、concepts、project、language 等过滤条件进行排序和截断。
- 对短 query 或泛词 query 做 query rewrite / query expansion，减少噪声召回。
- smart-search 增加 LLM 二次过滤，只保留真正支撑回答的 evidence。

### 多语言记忆检索

系统必须支持中文、英文和中英混合内容。存储层保留原文，不默认翻译记忆内容。

多语言策略：

- 每条 observation、memory、summary 和 Wiki 页面保存 `language` 字段，取值可为 `zh`、`en`、`mixed`、`unknown`。
- `searchable_text` 保留原文，并可附加规范化后的 `search_terms`。
- 英文、文件名、函数名、错误码和命令片段主要依赖 FTS5 精确检索。
- 中文自然语言和跨语言查询主要依赖 LanceDB 语义检索。
- 对中文或中英混合文本，系统应生成额外 n-gram 或关键词 search terms，提高 FTS5 召回率。
- embedding model 应优先选择支持多语言语义检索的模型。

第一版不做全量自动翻译，避免引入额外成本、延迟和翻译噪声。后续可以为跨语言检索增加 query translation 或 bilingual expansion。

### 多语言重复与合并

中文、英文和中英混合内容可能表达同一条事实。系统不能只依赖字符串 hash 判断重复，因为跨语言同义内容通常文本完全不同。

第一版策略：

- 保留原始语言内容，不自动翻译覆盖。
- `memory` 预留 `canonicalId`、`duplicateOf`、`relations` 字段。
- `relations` 后续可表达 `duplicate`、`complement`、`supersedes`、`contradicts`、`related_to`。
- memory core 阶段不自动合并跨语言重复，避免误删或误合并。

后续 RAG/governance 阶段再实现近似重复检测：

1. 新 memory 写入后生成 embedding。
2. 通过 LanceDB 查找语义相近的已有 memory。
3. 结合 concepts、files、type、project 和时间信息筛选候选。
4. 必要时由 LLM 判断候选关系是 duplicate、complement、supersedes、contradicts 还是 related_to。
5. 系统根据关系创建 canonical memory、标记 duplicate 或保留并建立 relation。

### RAG 更新机制

RAG 索引采用“写入同步更新关键词索引，向量索引异步补齐，启动时可重建”的机制。

写入链路：

1. agent 通过 CLI 或 REST 写入 observation 或 memory。
2. 系统保存原始记录。
3. 系统生成 `searchable_text`。
4. 系统同步写入 SQLite FTS5，让关键词搜索立即可用。
5. 系统创建 `embedding_update_job`，由后台 worker 调用 embedding provider 并把向量写入 LanceDB。
6. 系统返回写入成功，不等待 embedding 完成。

派生内容更新链路：

1. LLM 生成 summary 后，系统为 summary 写入 FTS5，并创建 embedding 更新任务。
2. Wiki 页面创建或更新后，系统为 Wiki 页面写入 FTS5，并创建 embedding 更新任务。
3. memory 被删除、替换或标记过期时，系统同步失效对应 FTS5 记录和 LanceDB 向量记录，并写入 audit。

启动修复链路：

1. 服务启动时加载已有索引状态。
2. 如果发现 FTS5 缺失、LanceDB 向量缺失、embedding model 不一致或索引版本过旧，系统标记需要 repair。
3. repair worker 分批补建缺失索引。
4. 用户也可以通过 CLI 或 REST 手动触发重建。

CLI：

- `agentmemory index status`
- `agentmemory index rebuild`
- `agentmemory index repair`

REST：

- `GET /agentmemory/index/status`
- `POST /agentmemory/index/rebuild`
- `POST /agentmemory/index/repair`

索引任务字段：

- `id`
- `type`: `embedding_update`、`fts_rebuild`、`index_repair`
- `targetType`: `observation`、`memory`、`summary`、`wikiPage`
- `targetId`
- `status`: `pending`、`running`、`done`、`failed`
- `attempts`
- `lastError`
- `createdAt`
- `updatedAt`

### LLM Wiki 实现

LLM Wiki 是 RAG 之上的长期知识沉淀思想。它不是把所有检索结果临时塞进 prompt，也不是只维护几篇静态页面；它的目标是让 LLM 持续把 agent 的观察、会话摘要、显式记忆和检索 evidence 提炼成可读、可引用、可演化、可检索的稳定知识层。

长期目标分层：

1. Raw layer：保存 observation、memory、summary 等原始 evidence。
2. Distilled layer：提炼稳定事实、流程模式、经验教训和阶段性工作结晶。
3. Synthesis layer：把 distilled knowledge 聚合成 Wiki 页面、反思 insight 和后续知识图谱。
4. Retrieval layer：让 search、smart-search、context、Skill 和 Viewer 使用这些长期知识。

第一版不一次性实现完整知识沉淀系统，而是先实现 Wiki 页面、Wiki update job 和最小 distilled knowledge，作为长期知识层的入口。当前最小 distilled knowledge 已覆盖 semantic、procedural、lesson 和 crystal 四类记录；后续 change 再补去重合并、reinforce/decay、crystal 稳定边界、reflect insights 和知识图谱。

第一版 Wiki 页面结构：

- `id`
- `title`
- `topic`
- `content`
- `sourceIds`
- `confidence`
- `createdAt`
- `updatedAt`

Wiki 更新流程：

1. 新 observation、memory 或 summary 进入系统后，后台任务判断它是否影响已有 topic。
2. LLM 根据新证据生成 Wiki update proposal，输出可解析的结构化内容。
3. 系统将 proposal 应用到对应 Wiki 页面，或创建新页面。
4. 每次更新必须保留 `sourceIds` 和 audit 记录。
5. Viewer 展示 Wiki 页面正文、来源引用和更新时间。

第一版 Wiki 页面可以先固定为几类稳定入口：

- 个人偏好
- 项目概览
- 技术决策
- 常见问题和修复经验
- 文件和模块说明
- 工作流习惯

这些固定页面不是最终的完整 LLM Wiki，只是 P0 的聚合视图，避免早期让模型自由创建大量碎片页面。长期上，Wiki 页面应主要从 distilled layer 聚合生成，而不是每条 evidence 都直接改写页面。

当前已落地的知识沉淀方向：

- Semantic facts：稳定事实，例如项目采用的技术栈、核心约束和已确认决策。
- Procedural patterns：做事流程，例如验收、归档、修复、搜索和调试习惯。
- Lessons：经验教训，当前保留 confidence 和 sourceIds，后续补 reinforce/decay。
- Crystals：把 evidence 压缩为阶段性摘要，当前为最小 digest，后续补按 session/change/source group 的稳定边界和 outcome/files/lessons 结构。
- Reflect insights：定期从 facts、patterns、lessons、crystals 和 graph 中归纳更高层 insight。

#### LLM Wiki 待优化

当前 distilled knowledge 已能从 evidence 生成 semantic、procedural、lesson 和 crystal 记录，但第一版还缺少去重、合并和强化机制。多次 `wiki update` 或 `wiki rebuild --all` 处理同一批 `sourceIds` 时，可能生成内容相近的重复 records；不同 topic job 也可能对同一条 evidence 重复 distill。

后续需要优化：

- 以 `kind + normalized content` 或 `kind + sourceIds + content fingerprint` 做精确去重。
- 对相似内容使用 embedding similarity 或 LLM 判断合并，而不是新增重复记录。
- 为 lessons 增加 `reinforcements`、`lastReinforcedAt` 和 confidence strengthen/decay。
- 为 crystals 增加按 session/change/source group 的稳定生成边界，避免每个 topic rebuild 都生成一条近似 crystal。
- Wiki rebuild 应优先复用已有 distilled knowledge，只在发现缺失或过期时再 distill。

这样 RAG 负责“找证据”，LLM Wiki 思想负责“把证据沉淀为稳定知识”，Wiki 页面负责“给 agent 和用户一个可读入口”。

### LLM Wiki 更新机制

LLM Wiki 采用“写入后入队，后台处理，定时补偿，手动可重建”的机制。

入队规则：

1. observation 保存成功后，系统创建 `wiki_update_job`。
2. memory 保存成功后，系统创建 `wiki_update_job`。
3. session summary 生成后，系统创建 `wiki_update_job`。
4. 如果同一 topic 已有 pending job，系统可以合并 source ids，避免短时间内重复调用 LLM。

后台处理：

1. worker 读取 pending jobs。
2. worker 收集 job 关联的 observation、memory、summary 和现有 Wiki 页面。
3. LLM 判断这些证据属于哪个 topic。
4. LLM 输出结构化 update proposal。
5. 系统校验 proposal，应用到 Wiki 页面或创建新页面。
6. 系统写入 audit，并为变更后的 Wiki 页面触发 RAG 索引更新。

定时补偿：

1. 周期性重试 failed jobs。
2. 扫描长时间未整理的 observation、memory 和 summary。
3. 压缩过长 Wiki 页面。
4. 标记低 confidence 或来源不足的页面。

手动入口：

- `agentmemory wiki update`
- `agentmemory wiki rebuild --topic <topic>`
- `agentmemory wiki rebuild --all`

REST：

- `POST /agentmemory/wiki/update`
- `POST /agentmemory/wiki/rebuild`

Wiki 更新任务字段：

- `id`
- `sourceIds`
- `topic`
- `status`: `pending`、`running`、`proposed`、`applied`、`failed`
- `proposal`
- `attempts`
- `lastError`
- `createdAt`
- `updatedAt`

### LLM 和 Embedding

- LLM API：OpenAI-compatible Chat Completions。
- Embedding API：OpenAI-compatible Embeddings。
- SDK：官方 `openai` Python SDK，配置 `base_url` 和 `api_key`。
- 测试：使用真实 OpenAI-compatible LLM provider 和 embedding provider，测试前必须配置 base URL、model 和 API key。

配置项：

- `AGENTMEMORY_LLM_BASE_URL`
- `AGENTMEMORY_LLM_MODEL`
- `AGENTMEMORY_LLM_API_KEY`
- `AGENTMEMORY_EMBEDDING_BASE_URL`
- `AGENTMEMORY_EMBEDDING_MODEL`
- `AGENTMEMORY_EMBEDDING_API_KEY`

选择原因：OpenAI-compatible 形态既能直接支持 OpenAI，也能接入兼容协议的模型服务。LLM 和 embedding 分开配置，方便用户按成本和效果独立选择模型。

### 知识图谱

- 第一版图谱定位：轻量关系图 Viewer。
- 当前实现：Viewer 从现有 sessions、memories、summaries、files、concepts、Wiki 页面和 distilled knowledge 派生关系图，不依赖独立持久化 graphNodes/graphEdges。
- 后续增强：可增加 LLM 图谱抽取、`KV.graphNodes`、`KV.graphEdges` 和图谱查询 API。
- 图谱用途：查看、导航、发现关联，不作为第一版搜索排序的核心依赖。

第一版节点类型：

- `project`
- `session`
- `file`
- `concept`
- `memory`
- `wikiPage`

第一版边类型：

- `mentions`
- `derived_from`
- `related_to`
- `belongs_to`

### 测试

- 测试框架：pytest。
- HTTP 测试：FastAPI TestClient 或 httpx。
- CLI 测试：Typer CliRunner。
- 前端测试：Playwright 用于关键页面截图和交互检查。

测试重点：

- 核心函数单元测试。
- LLM/embedding 真实 provider 集成测试。
- REST API 集成测试。
- CLI JSON 输出测试。
- Viewer 搜索、Wiki、health 和图谱加载测试。

### 打包和发布

- Python 打包：pyproject.toml + hatchling。
- 前端构建：Vite build，产物由服务端静态托管。
- 发布形态：Python package，提供 `agentmemory` CLI entry point。
- 本地运行：`agentmemory serve` 启动 API 和 Viewer。

## 8. 状态模型

P0 核心 scope：

- `KV.sessions`：会话元数据，包含开始时间、结束时间、项目路径、统计信息。
- `KV.observations(sessionId)`：原始观察记录，包含工具执行、事件和文本摘要。
- `KV.memories`：用户显式保存或 LLM 提炼出的长期记忆。
- `KV.summaries`：observation summary 和 session summary。
- `KV.wikiPages`：LLM 维护的个人知识库页面，包含主题、正文、来源引用和更新时间。
- `memory.relations`：长期记忆关系预留字段，用于后续重复、补充、替代、冲突和相关关系治理。
- Viewer 关系图：当前从已有 records 派生，不要求独立 `KV.graphNodes` 或 `KV.graphEdges`。
- `KV.audit`：保存、删除、导入、导出等状态变更记录。

ID 规则：

- 唯一实体使用 `generateId(prefix)`。
- 内容去重使用 `fingerprintId(prefix, content)`。
- 状态变更的时间戳应在一次操作开始时捕获并复用。

## 9. 性能与触发策略

AgentMemory 要求真实 AI provider 可用，但这不等于每一步都调用 LLM。第一版必须采用低频、关键节点触发策略，避免 Skill 让 agent 工作流变慢。

### 当前版本策略

- `agentmemory observe` 会触发 LLM processing，因此只能在阶段性节点调用。
- `agentmemory remember` 只在用户明确要求保存或形成稳定决策时调用。
- `search` / `smart-search` / `context` 只在任务开始、历史决策不确定、用户提到“之前/上次/记得”或修改关键模块前调用。
- Skill 不允许要求 agent 在每次工具调用、每次文件读取、每次编辑或每次测试后调用 AgentMemory。
- 同一个任务中，普通 observation 应合并成阶段总结；除非发生关键事件，不要连续高频写入。

### 后续 Hook 策略

Hook 版本如果未来加入，不能默认把每个 PostToolUse 事件同步送入 LLM。可接受策略是：

- 默认不启用 hook。
- hook 默认只记录轻量原始事件，LLM processing 走队列、批处理或显式开关。
- PreToolUse / SessionStart 上下文注入默认关闭，必须显式启用。
- 对频繁事件设置节流、去重、超时和失败吞吐策略。

这样可以保持 AI native 的产品约束，同时避免每一步都产生模型延迟和 token 成本。

## 10. 接口形态

### Skill

Skill 是第一版的主要 agent 接入层。它不直接保存数据，而是告诉 agent：

- 什么时候调用 `agentmemory remember` 保存长期记忆。
- 什么时候调用 `agentmemory search` 或 `agentmemory smart-search` 搜索历史经验。
- 什么时候调用 `agentmemory context` 获取可注入上下文。
- 什么时候调用 `agentmemory wiki` 查看或更新个人知识库页面。
- CLI 失败时如何直接调用 REST API。

### CLI

CLI 是最通用的 agent 调用入口。P0 命令：

- `agentmemory serve`
- `agentmemory observe`
- `agentmemory remember`
- `agentmemory search`
- `agentmemory smart-search`
- `agentmemory context`
- `agentmemory wiki`
- `agentmemory export`
- `agentmemory doctor`

CLI 默认调用本地 REST API，也可以在必要时走本地函数实现。

### Skill 设计

第一版提供项目 Skill 文件，建议路径为：

```text
skills/agentmemory/SKILL.md
```

Skill 的作用不是直接保存数据，而是把 AgentMemory 变成 agent 的行为协议。所有支持读取 Skill 的 agent 都应按该文件决定什么时候查询、保存、记录和读取上下文。

Skill 文件应包含以下部分：

#### 1. 使用前提

- 默认优先调用 CLI。
- CLI 不可用时，使用 REST API 兜底。
- 所有查询类命令优先使用 `--json`，方便 agent 解析。
- 不要把没有证据来源的 LLM 结论写成长期记忆。

#### 2. 必须查询的场景

agent 在以下场景 SHOULD 先查询记忆：

- 开始一个新任务时。
- 进入已有项目或长时间未处理的项目时。
- 用户提到“之前”、“上次”、“记得”、“按我们以前的方式”时。
- 修改不熟悉的文件、模块或架构前。
- 遇到报错、测试失败或依赖问题时。
- 做技术选型、接口设计、数据模型变更前。
- 大规模重构或跨模块改动前。

推荐命令：

```bash
agentmemory search "<task or question>" --mode hybrid --json
agentmemory smart-search "<task or question>" --mode hybrid --json
agentmemory context "<task or question>" --project "<project-path>" --json
```

#### 3. 必须保存的场景

agent 在以下场景 SHOULD 保存长期 memory：

- 用户明确说“记住”、“保存”、“以后都这样”。
- 确定了技术选型、架构决策或接口契约。
- 发现稳定的用户偏好或项目约定。
- 修复了非显而易见的问题。
- 发现常见错误原因和解决方式。
- 形成可复用的工作流、测试方式或排障步骤。

推荐命令：

```bash
agentmemory remember \
  --type decision \
  --content "<stable memory>" \
  --concepts "<comma-separated concepts>" \
  --files "<comma-separated files>" \
  --json
```

#### 4. 必须记录 observation 的场景

agent 在以下场景 SHOULD 记录 observation：

- 完成一次有价值的代码阅读或探索。
- 完成一个修改并验证结果。
- 发现一个问题但暂时没有解决。
- 完成阶段性任务总结。
- 用户纠正了 agent 的理解或方向。

推荐命令：

```bash
agentmemory observe \
  --type work-summary \
  --content "<what happened, what was learned, files touched, result>" \
  --json
```

#### 5. Wiki 使用规则

agent 在需要稳定项目知识时 SHOULD 查询 Wiki：

```bash
agentmemory wiki pages --json
agentmemory wiki knowledge --json
agentmemory wiki jobs --json
```

当用户要求整理当前知识库，或 agent 发现 Wiki 明显过期时，可以触发：

```bash
agentmemory wiki update --json
agentmemory wiki rebuild --topic "<topic>" --json
```

#### 6. 返回结果使用规则

`search`、`smart-search` 和 `context` 返回结构化 JSON。agent 应遵守：

- 优先读取 `answer` 快速理解结论。
- 重要决策必须查看 `evidence` 和 `sourceIds`。
- 如果 `confidence` 低或 evidence 不足，应继续搜索或说明不确定。
- 只有在证据足够稳定时，才调用 `remember` 保存长期记忆。
- 需要注入 prompt 的内容优先使用 `context` 字段。

#### 7. REST 兜底

CLI 不可用时，Skill 应指导 agent 使用 REST：

```bash
curl -s http://localhost:3111/agentmemory/smart-search \
  -H "Content-Type: application/json" \
  -d '{"query":"<question>","limit":5}'
```

REST 方式主要作为 CLI 不可用时的本地兜底入口。服务化鉴权可在后续接入。

### REST

REST 路径统一以 `/agentmemory/*` 开头。当前实现重点是本地服务、字段校验、健康检查和敏感配置脱敏；Bearer token 鉴权作为后续服务化能力。

P0 端点：

- `POST /agentmemory/observe`
- `POST /agentmemory/remember`
- `POST /agentmemory/search`
- `POST /agentmemory/smart-search`
- `POST /agentmemory/context`
- `GET /agentmemory/wiki/pages`
- `GET /agentmemory/wiki/jobs`
- `GET /agentmemory/wiki/knowledge`
- `POST /agentmemory/wiki/update`
- `POST /agentmemory/wiki/rebuild`
- `GET /agentmemory/export`
- `POST /agentmemory/forget`
- `GET /agentmemory/health`

## 11. 配置

P0 配置：

- `AGENTMEMORY_HOST`
- `AGENTMEMORY_PORT`
- `AGENTMEMORY_DB_PATH`
- `AGENTMEMORY_VECTOR_DB_PATH`
- `AGENTMEMORY_SECRET`
- `AGENTMEMORY_LLM_BASE_URL`
- `AGENTMEMORY_LLM_MODEL`
- `AGENTMEMORY_LLM_API_KEY`
- `AGENTMEMORY_EMBEDDING_BASE_URL`
- `AGENTMEMORY_EMBEDDING_MODEL`
- `AGENTMEMORY_EMBEDDING_API_KEY`

首版 provider 使用 OpenAI-compatible API 形态，默认支持 OpenAI，也允许接入兼容 OpenAI 协议的模型服务。高级配置可以后续增加上下文注入开关、自动压缩策略、向量维度、rerank model 和图谱抽取策略。

## 12. 开发流程

项目按正规产品开发流程推进：

1. 需求定义：明确用户、场景、P0/P1/P2 范围和验收标准。
2. 技术选型：确定语言、框架、状态层、RAG、LLM Wiki、LLM provider、embedding provider、CLI 框架和测试框架。
3. 规格设计：为采集、搜索、接口、治理分别定义可测试需求。
4. 实现拆解：按状态层、provider、核心函数、CLI、REST、Viewer 和测试推进。
5. 验收测试：完成 P0 端到端路径，确认 agent 能写入、搜索、保存、导出和审计。
6. 迭代扩展：再加入 P1/P2 的高级记忆、图谱、多 agent 协作和评估体系。

## 13. 质量要求

- 所有核心能力必须有单元测试。
- REST、CLI 和 Viewer 必须有集成测试。
- LLM 相关逻辑必须通过真实 OpenAI-compatible provider 测试。
- 错误必须结构化返回，不允许未处理异常泄露到调用方。
- 删除和导入导出必须写 audit。
- 高级能力关闭时，P0 核心功能必须可用。
