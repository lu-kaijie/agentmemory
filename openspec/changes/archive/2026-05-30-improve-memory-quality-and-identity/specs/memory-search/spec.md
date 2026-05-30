## ADDED Requirements

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
