## ADDED Requirements

### Requirement: Keyword Search

系统 SHALL 支持对已索引的 observation、memory 和 summary 执行关键词检索。

关键词检索 MUST 使用 SQLite FTS5。搜索结果 MUST 包含 `sourceType`、`sourceId`、`content`、`score`、`language`、`project`、`files`、`concepts` 和 `createdAt`。

#### Scenario: Search indexed memories by keyword

- **WHEN** 客户端提交关键词查询
- **THEN** 系统返回匹配的 observation、memory 或 summary 搜索结果

### Requirement: Vector Search

系统 SHALL 支持对已索引的 observation、memory 和 summary 执行向量语义检索。

向量检索 MUST 使用配置的 embedding provider 生成 query embedding，并在 LanceDB 中检索语义相近记录。

#### Scenario: Search indexed memories by meaning

- **WHEN** 客户端提交自然语言查询并请求 vector search
- **THEN** 系统返回语义相近的搜索结果和 source ids

### Requirement: Hybrid Search

系统 SHALL 支持混合检索，合并关键词检索和向量检索结果。

Hybrid search MUST 去重同一 `sourceType` + `sourceId`，并返回合并后的 ranked results。系统 MUST 保留每条结果的匹配来源信息。

#### Scenario: Merge keyword and vector results

- **WHEN** 同一 source 同时出现在关键词结果和向量结果中
- **THEN** 系统只返回一条合并结果，并保留两种匹配来源

### Requirement: Smart Search Explanation

系统 SHALL 支持 `smart-search`，用 LLM 基于检索证据生成简短解释。

Smart search response MUST 包含 `answer`、`results`、`evidence` 和 `context`。`evidence` MUST 引用返回结果中的 source ids。LLM MUST NOT 在没有检索结果支持时编造结论。

#### Scenario: Explain search results with evidence

- **WHEN** hybrid search 返回至少一条结果
- **THEN** 系统调用 LLM 生成基于结果的解释，并返回 evidence/source ids

#### Scenario: No results explanation

- **WHEN** hybrid search 没有返回结果
- **THEN** 系统返回空 results 和说明未找到相关记忆的 answer

### Requirement: Search Modes

系统 SHALL 支持 `keyword`、`vector` 和 `hybrid` 搜索模式。

默认 search mode MUST 为 `keyword`。默认 smart-search mode MUST 为 `hybrid`。

#### Scenario: Keyword mode does not call embedding

- **WHEN** 客户端使用 `keyword` mode 调用 search
- **THEN** 系统只执行 FTS5 检索，不调用 embedding provider

#### Scenario: Hybrid mode uses both indexes

- **WHEN** 客户端使用 `hybrid` mode 调用 search
- **THEN** 系统执行 FTS5 和 LanceDB 检索并合并结果
