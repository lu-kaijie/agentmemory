## ADDED Requirements

### Requirement: Keyword Search

系统 SHALL 提供关键词搜索能力，支持按 `query`、`limit`、`sessionId` 和项目路径过滤 observation、memory 和 summary。

#### Scenario: Search by file name

- **WHEN** 用户搜索一个曾出现在 observation 或 memory 中的文件名
- **THEN** 系统返回包含该文件名的相关结果，并按相关性排序

#### Scenario: Search with limit

- **WHEN** 用户提交 `limit` 参数
- **THEN** 系统返回不超过该数量的搜索结果

### Requirement: Smart Search

系统 SHALL 提供 `mem::smart-search` 入口，P0 MUST 使用关键词召回、embedding 召回和 LLM 辅助结果解释。

#### Scenario: Smart search returns structured results

- **WHEN** CLI 或 REST client 调用智能搜索
- **THEN** 系统返回 JSON 结果，包含 LLM 综合结论、证据列表、匹配分数、结果来源和简要匹配说明

### Requirement: Embedding Search

系统 SHALL 从第一版支持 OpenAI-compatible embedding provider，并将 memory、summary、Wiki 页面和重要 observation 写入向量索引。

#### Scenario: Semantic query finds related memory

- **WHEN** 用户使用自然语言查询某个语义相关但关键词不同的主题
- **THEN** 系统通过 embedding 召回相关 memory、summary 或 Wiki 页面

### Requirement: Context Retrieval

系统 SHALL 支持按 token budget 输出适合 agent 注入上下文的记忆片段，并在 LLM provider 可用时压缩为更紧凑的上下文。

#### Scenario: Context under token budget

- **WHEN** 用户请求某个 query 的上下文且提供 token budget
- **THEN** 系统返回不超过预算的上下文内容，并优先包含高相关 memory

#### Scenario: LLM compresses context

- **WHEN** 搜索结果超过 token budget 且 LLM provider 可用
- **THEN** 系统返回 LLM 压缩后的上下文，并保留引用来源 id

### Requirement: Search Upgrade Path

系统 MUST 保持智能搜索接口稳定，使后续加入 embedding、向量索引和图谱权重时不破坏调用方。

#### Scenario: Vector provider disabled

- **WHEN** embedding provider 未配置或被关闭
- **THEN** 智能搜索仍然返回关键词召回和 LLM 辅助解释结果，并在 health 中报告 embedding 不可用

### Requirement: RAG Index Updates

系统 SHALL 在 observation、memory、summary 和 Wiki 页面变化时维护 RAG 索引。

系统 MUST 在 observation 或 memory 写入后同步更新关键词索引，并创建 embedding 更新任务。系统 MUST 在 summary 或 Wiki 页面创建、更新、删除或过期时同步维护关键词索引和 embedding 索引状态。

#### Scenario: Observation is immediately searchable by keyword

- **WHEN** agent 通过 CLI 或 REST 写入 observation
- **THEN** 系统保存 observation，并同步写入关键词索引

#### Scenario: Embedding update is asynchronous

- **WHEN** agent 写入 observation 或 memory
- **THEN** 系统创建 embedding 更新任务，并在不等待 embedding 完成的情况下返回写入成功

#### Scenario: Index repair detects missing embedding

- **WHEN** 定时 repair 发现某条 memory 缺少当前 embedding model 的向量
- **THEN** 系统创建或重试 embedding 更新任务

#### Scenario: Deleted memory is removed from active search

- **WHEN** 用户删除或过期某条 memory
- **THEN** 系统将该 memory 从活跃关键词和向量检索结果中移除，并保留 audit

### Requirement: Multilingual Memory Retrieval

系统 SHALL 支持中文、英文和中英混合记忆的存储与检索。

系统 MUST 保留原始语言内容。系统 MUST 为可检索对象记录 `language` 字段。系统 SHOULD 为中文或中英混合内容生成额外 n-gram 或关键词 `search_terms`，用于提升 FTS5 关键词召回。embedding provider MUST 优先选择支持多语言语义检索的模型。

#### Scenario: Chinese memory is searchable semantically

- **WHEN** 用户用中文自然语言查询历史记忆
- **THEN** 系统通过 LanceDB 语义召回相关中文或中英混合记忆

#### Scenario: English technical term remains searchable

- **WHEN** 用户搜索文件名、函数名、错误码或英文技术术语
- **THEN** 系统通过 FTS5 召回包含该精确术语的结果

#### Scenario: Mixed language content adds search terms

- **WHEN** 系统索引中英混合 memory
- **THEN** 系统保存原文，并生成可用于关键词检索的补充 search terms
