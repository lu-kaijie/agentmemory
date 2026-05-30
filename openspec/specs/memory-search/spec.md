# memory-search Specification

## Purpose

定义 AgentMemory 对 observation、memory 和 summary 的关键词检索、向量检索、混合检索和基于证据的智能解释能力。
## Requirements
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

### Requirement: Search Relevance Gate

系统 SHALL 在返回 search、smart-search 和 context evidence 前执行相关性门控。

Search request MUST 支持可选 `minScore` 和 `matchMode`。`matchMode` MUST 支持 `auto`、`any`、`all` 和 `phrase`。系统 MUST 为 keyword、vector 和 hybrid mode 应用默认相关性策略，过滤低置信或仅由泛词触发的弱相关结果。系统 MUST 在结果中保留 score 和 matchSources，供调用方判断证据质量。

#### Scenario: Filter weak keyword matches

- **WHEN** 用户查询只包含泛词或弱匹配内容
- **THEN** 系统过滤低相关结果，或返回明显低 confidence 的空/少量结果

#### Scenario: Honor strict match mode

- **WHEN** 用户指定 `matchMode=all` 或 `matchMode=phrase`
- **THEN** keyword search 只返回满足全部关键术语或短语匹配的结果

#### Scenario: Keep explicit broad recall

- **WHEN** 用户指定 `matchMode=any` 且降低 `minScore`
- **THEN** 系统允许返回更宽的召回结果

### Requirement: Hybrid Reranking

系统 SHALL 对 hybrid search 结果执行去重、加权合并和 rerank。

Hybrid rerank MUST 提升同时命中 keyword 和 vector 的结果，MUST 结合 sourceType、project、language、concepts、files 和 createdAt 进行稳定排序。Hybrid rerank MUST 降低只命中泛词 keyword 且缺少 metadata 支撑的结果。

#### Scenario: Prefer dual matched result

- **WHEN** 两条结果分数接近且其中一条同时命中 keyword 和 vector
- **THEN** hybrid search 排名优先展示同时命中的结果

#### Scenario: Respect metadata filters

- **WHEN** 用户指定 project、language 或 sourceTypes
- **THEN** hybrid rerank 只在符合过滤条件的结果中排序

### Requirement: Smart Search Evidence Filtering

系统 SHALL 只基于通过相关性门控的 evidence 生成 smart-search answer。

Smart search MUST NOT 把被 relevance gate 过滤的结果传给 LLM 作为 evidence。若门控后 evidence 不足，smart-search MUST 返回低置信或未找到相关记忆的 answer。

#### Scenario: Smart search ignores weak evidence

- **WHEN** 原始召回包含低相关结果但 relevance gate 全部过滤
- **THEN** smart-search 不使用这些结果生成事实性回答

#### Scenario: Smart search uses filtered evidence

- **WHEN** relevance gate 保留高相关 evidence
- **THEN** smart-search answer 只引用保留下来的 source ids

### Requirement: Search Modes

系统 SHALL 支持 `keyword`、`vector` 和 `hybrid` 搜索模式。

默认 search mode MUST 为 `keyword`。默认 smart-search mode MUST 为 `hybrid`。

#### Scenario: Keyword mode does not call embedding

- **WHEN** 客户端使用 `keyword` mode 调用 search
- **THEN** 系统只执行 FTS5 检索，不调用 embedding provider

#### Scenario: Hybrid mode uses both indexes

- **WHEN** 客户端使用 `hybrid` mode 调用 search
- **THEN** 系统执行 FTS5 和 LanceDB 检索并合并结果

### Requirement: Search Wiki Pages

系统 SHALL 支持搜索 Wiki pages。

Search sourceTypes MUST 支持 `wikiPage`。Keyword、vector 和 hybrid search MUST 能返回匹配的 Wiki page results，并保留 Wiki page source id。

Search sourceTypes MUST 支持 `knowledge`。Keyword、vector 和 hybrid search MUST 能返回匹配的 distilled knowledge results，并保留 knowledge source id。

#### Scenario: Keyword search finds wiki page

- **WHEN** 用户使用 keyword search 查询 Wiki 页面中的术语
- **THEN** 系统返回 sourceType 为 `wikiPage` 的结果

#### Scenario: Vector search finds wiki page

- **WHEN** 用户使用自然语言 vector search 查询 Wiki 页面语义相关内容
- **THEN** 系统返回 sourceType 为 `wikiPage` 的结果

#### Scenario: Filter search to wiki pages

- **WHEN** 用户指定 sourceTypes 包含 `wikiPage`
- **THEN** 系统只返回符合 source type 过滤条件的结果

#### Scenario: Search distilled knowledge

- **WHEN** 用户搜索已沉淀的 semantic、procedural、lesson 或 crystal 内容
- **THEN** 系统返回 sourceType 为 `knowledge` 的结果

#### Scenario: Filter search to distilled knowledge

- **WHEN** 用户指定 sourceTypes 包含 `knowledge`
- **THEN** 系统只返回符合 source type 过滤条件的 results
