## Context

当前仓库处于产品初始化阶段，尚未存在可运行服务。目标产品是一个 AI native 个人长期记忆平台：agent 是首要用户，LLM 是核心处理层，所有能力都要能被 Skill 指导并通过 CLI 或 API 调用。agent 可以把会话事件、工具调用和用户明确保存的内容写入服务，并在未来会话中通过 CLI 或 REST API 搜索、导出、审计和复用这些记忆。

系统面向三类使用者，其中 agent 是第一优先级：

- AI agent：通过 Skill 获得行为规则，通过 CLI 或 REST 自动写入、搜索、压缩和注入上下文。
- 开发者：通过 REST API、Viewer 和导出文件检查记忆状态。
- 维护者：通过审计、健康检查和配置开关控制数据治理与高级能力。

约束：

- P0 必须从第一版接入 OpenAI-compatible LLM provider 和 embedding provider，用于摘要、记忆提炼、智能搜索解释、上下文压缩和语义召回。
- REST、CLI、Viewer 和后台任务不得各自直接操作底层数据库，必须通过内部 `mem::*` 能力访问状态。
- 高级图谱和 embedding 能力必须可配置关闭，关闭后不得影响 LLM 辅助保存、搜索、导出等核心流程。

## Goals / Non-Goals

**Goals:**

- 建立从需求、规格、技术设计到任务拆解的 AI native 产品开发基线。
- 实现一个 Python/FastAPI 服务架构，包含内部函数层、状态层、CLI adapter、REST adapter、Viewer 和测试。
- P0 支持 observation 采集、LLM 摘要与记忆提炼、显式 memory 保存、关键词搜索、embedding 搜索、LLM 辅助智能搜索、Wiki 页面维护、CLI/API 接入、Web Viewer、导出、删除审计和健康检查。
- P1 支持 session start/end、摘要、时间线、关系、Viewer 和 import/export 兼容。
- P2 支持知识图谱增强、多模态和行动编排等可选能力。

**Non-Goals:**

- P0 不要求实现复杂知识图谱、MCP adapter 或 Hook adapter。
- P0 不要求多租户计费、企业权限管理或云托管平台。
- P0 不要求兼容所有 agent 客户端的专有扩展，只需提供标准 Skill、CLI 和 REST API。
- P0 不实现前端复杂可视化，只保留 Viewer 的最小可用路径。

## Decisions

### 1. 产品架构采用 agent-first 和 LLM-first

agent 是首要调用方，因此接口设计优先满足 Skill 可描述、CLI 可执行、API 可直接调用、上下文可注入和结构化 JSON 返回。LLM 从第一版进入主链路，负责摘要、提炼、解释、压缩和 Wiki 页面维护，而不是后期附加功能。

备选方案：

- 先做普通 CRUD 服务再接 AI：短期简单，但无法验证 agent 工作流中的真实价值。
- 只做聊天式 UI：不适合 coding agent 自动调用，也难以嵌入现有开发链路。

### 2. 使用 Python + FastAPI 作为初始技术栈

选择 Python 3.11+ 和 FastAPI 是因为 LLM、embedding、RAG、文本处理、后台任务和数据处理生态更完整。FastAPI + Pydantic 能同时约束 REST payload、CLI 输入和内部函数 schema。

备选方案：

- TypeScript/Node.js：CLI、网页和 agent 工具生态成熟，但 RAG、embedding 和文本处理生态不如 Python 直接。
- Rust：性能和单文件分发优秀，但产品迭代初期开发成本偏高。

具体选型：

- 包管理：uv。
- 数据模型：Pydantic v2。
- 配置：pydantic-settings。
- 测试：pytest。

### 3. 采用分层架构而不是端点直连数据库

核心分层：

- `agentmemory/functions/`：内部业务能力，例如 `mem::observe`、`mem::remember`、`mem::search`。
- `agentmemory/state/`：状态 schema、状态访问、索引持久化和审计写入。
- `agentmemory/api/`：REST adapter，只做认证、校验、白名单字段和调用内部能力。
- `agentmemory/cli.py`：CLI adapter，默认调用 REST API，供 Skill 和 agent shell 工具使用。
- `skills/`：项目 Skill，指导 agent 保存、搜索、更新 Wiki 和注入上下文。
- `agentmemory/viewer/`：轻量 Viewer 静态资源和健康检查页面。

这样 REST、CLI 和 Viewer 的行为能保持一致，测试也可以优先覆盖内部 `mem::*` 函数。

### 4. REST 使用 FastAPI，参数校验使用 Pydantic

FastAPI 提供稳定的 HTTP 服务能力、自动 OpenAPI 文档和良好的类型标注体验。Pydantic 用于 REST body、CLI 参数和内部函数 payload 校验，减少各入口重复定义 schema。

备选方案：

- Flask：简单稳定，但类型、OpenAPI 和 schema 约束需要额外补充。
- Litestar：能力完整，但团队熟悉度和生态普及度不如 FastAPI。

### 5. CLI 使用 Typer

CLI 是第一版最重要的 agent 接入方式。使用 Typer 实现 `serve`、`observe`、`remember`、`recall`、`context`、`wiki`、`export`、`doctor`。默认输出人类可读文本，`--json` 输出结构化 JSON，方便 agent 解析。

### 6. Web Viewer 使用 Vite + React + React Flow

Viewer 第一版需要展示 sessions、memories、search、Wiki、health 和轻量知识图谱。Vite + React 足够轻，React Flow 可以快速实现节点、边、拖拽、缩放、点击详情、按类型过滤和一跳邻居展开。

备选方案：

- 手写 canvas：性能可控，但交互和维护成本更高。
- Cytoscape.js：图谱能力强，但 React Flow 更贴合第一版管理型 Viewer 的交互方式。

### 7. P0 状态层使用文件型 SQLite，外部只暴露 StateKV 抽象

SQLite 适合本地 agent 工作流，部署简单、便于导出和备份。代码只通过 `StateKV` 等价抽象访问 `KV.sessions`、`KV.observations`、`KV.memories`、`KV.audit` 等 scope，避免后续迁移数据库时影响边界层。

具体选型：

- SQLite 访问：SQLAlchemy 2.x。
- 关键词搜索：SQLite FTS5。
- 向量索引：LanceDB，本地嵌入式向量库，用于保存 embedding 并执行语义检索。

备选方案：

- JSON 文件：更简单，但并发、查询和一致性较弱。
- Postgres：适合多人服务化部署，但初始运维成本高。
- SQLite 手写向量表：依赖更少，但需要应用层逐一计算相似度，数据量增长后性能和维护性较差。
- Qdrant：功能完整，适合服务化和更大规模数据，但第一版需要额外服务，部署复杂度更高。

### 8. P0 搜索采用 BM25 + embedding + LLM 辅助解释

P0 的召回层同时实现关键词检索、embedding 检索和结构化过滤，保证既能精确命中文件名和术语，也能处理自然语言语义查询。LLM 从第一版介入，用于把 observation 压缩成摘要、从搜索结果中提炼回答、解释匹配原因、更新 Wiki 页面，并生成适合 agent 注入的上下文。后续再加入 graph weight、query expansion 和 rerank。

RAG 实现分为写入和检索两段：

- 写入时，observation、memory、summary 和 Wiki 页面都会生成可检索文本，写入 FTS5，并通过 embedding provider 写入 LanceDB。
- 检索时，FTS5 负责关键词召回，LanceDB 负责语义召回，智能搜索合并两路结果并保留 source ids。
- 生成时，LLM 只基于召回证据生成 answer、evidence、wikiPages 和 context，不允许丢失来源引用。

FTS5 是基于倒排索引和 BM25 排序的全文检索，不计算向量。LanceDB 是向量检索层，负责根据 query embedding 查找语义相近记录。

RAG 更新采用写入同步和后台补偿结合：

- observation 和 memory 写入后，系统同步写入 FTS5，使关键词检索立即可用。
- embedding 更新通过 `embedding_update_job` 异步执行，并写入 LanceDB，不阻塞写入请求。
- summary 或 Wiki 页面更新后，系统触发对应的索引更新。
- 删除、替换或过期记录时，系统同步失效 FTS5 和 LanceDB 向量记录。
- 服务启动时检查缺失索引、旧索引版本和 embedding model 变化，并触发 repair。
- CLI 和 REST 提供 index status、rebuild 和 repair 入口。

LLM Wiki 是 RAG 之上的知识沉淀层：

- 后台任务根据新 observation、memory 或 summary 判断是否影响已有 topic。
- LLM 输出结构化 Wiki update proposal。
- 系统应用 proposal 到 Wiki 页面，或创建新页面。
- 每次 Wiki 更新必须保留 source ids 和 audit 记录。
- 第一版主题包括个人偏好、项目概览、技术决策、常见问题、文件模块说明和工作流习惯。

LLM Wiki 更新采用 job 驱动：

- observation、memory 和 summary 进入系统后创建 `wiki_update_job`。
- worker 收集 job source ids 关联的证据和现有 Wiki 页面。
- LLM 判断 topic 并输出结构化 proposal。
- 系统校验 proposal 后应用到 Wiki 页面，或创建新页面。
- Wiki 页面变更后触发 RAG 索引更新。
- 定时任务负责重试 failed jobs、整理长时间未处理的内容、压缩过长页面。
- CLI 和 REST 提供 wiki update 和 rebuild 入口。

### 9. LLM provider 采用可插拔接口

系统定义 OpenAI-compatible `LLMProvider` 和 `EmbeddingProvider` 接口，P0 至少支持 OpenAI，并允许用户分别配置 LLM 和 embedding 的 base URL、model 和 API key。业务层不得直接调用供应商 SDK，必须通过 provider 接口完成 summarization、extraction、ranking explanation、context compression、wiki update 和 embedding。

具体选型：

- SDK：官方 `openai` Python SDK。
- LLM API：OpenAI-compatible Chat Completions。
- Embedding API：OpenAI-compatible Embeddings。
- 测试：fake LLM provider 和 fake embedding provider。

备选方案：

- 业务代码直接调用单一厂商 SDK：实现快，但后续迁移和测试困难。
- 只接 LLM 不接 embedding：能生成摘要，但语义召回质量不足，不符合个人知识库体验。

### 10. 轻量知识图谱作为 Viewer 导航能力

第一版提供轻量知识图谱 Viewer，但不把图谱作为搜索排序核心依赖。图谱数据由 LLM 从 memory、summary、Wiki 页面和重要 observation 中抽取，写入 `KV.graphNodes` 和 `KV.graphEdges`。

第一版节点类型包括 `project`、`session`、`file`、`concept`、`memory`、`wikiPage`。第一版边类型包括 `mentions`、`derived_from`、`related_to`、`belongs_to`。

### 11. 认证采用可选 Bearer token

当 `AGENTMEMORY_SECRET` 存在时，所有非公开 REST 端点必须校验 `Authorization: Bearer <secret>`。本地开发可以不设置 secret，CLI 调用远程或本地 REST 时必须支持读取并转发 secret。

### 12. 错误响应统一结构化

REST adapter 返回 `{ status_code, body, headers? }` 语义，HTTP body 使用 `{ error: { code, message, details? } }`。CLI 默认输出人类可读文本，带 `--json` 时输出结构化 JSON，避免未处理异常泄露到调用方。

## Risks / Trade-offs

- 状态 schema 过早复杂化 -> P0 只强制 `sessions`、`observations`、`memories`、`audit`，高级 scope 以可选模块加入。
- LLM provider 不可用导致核心智能能力失败 -> 启动健康检查报告 provider 状态；写入 observation 仍可成功，但摘要/提炼/Wiki 任务进入 pending 或 failed 状态并可重试。
- 搜索质量初期不够智能 -> P0 同时使用 BM25 和 embedding 召回，LLM 负责摘要、解释和上下文压缩，保留智能搜索入口以便后续无破坏升级。
- 本地 SQLite 并发写入冲突 -> 状态层集中写入、短事务和测试覆盖并发场景；后续服务化再迁移到 Postgres。
- CLI 和 REST 行为漂移 -> 所有 adapter 调用同一组 `mem::*` 函数，并用共享 schema 校验输入。

## Migration Plan

这是初始建设，无历史数据迁移。

实施顺序：

1. 创建项目骨架、包管理、测试框架和基础配置。
2. 实现 OpenAI-compatible LLM/embedding provider 接口、fake provider 和首个真实 provider 配置。
3. 实现状态层与核心内部函数。
4. 实现 LLM 摘要、记忆提炼、Wiki 更新和智能搜索解释流程。
5. 实现 CLI、REST adapter 和健康检查。
6. 实现 Skill 和 Web Viewer。
7. 补齐导出、审计、删除和 Web Viewer。
8. 增加测试、文档和本地运行脚本。

回滚策略：

- 每个阶段保持可运行和可测试。
- 高级能力通过配置开关关闭。
- 状态 schema 变更必须提供导出文件，便于回退到上一版本。
