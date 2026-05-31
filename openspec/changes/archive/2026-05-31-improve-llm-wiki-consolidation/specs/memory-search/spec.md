## ADDED Requirements

### Requirement: Search LLM Wiki Insights

系统 SHALL 支持搜索 LLM Wiki reflect insights。

Search sourceTypes MUST 支持 `insight`，keyword、vector 和 hybrid search MUST 能返回匹配的 insight results。Context MUST 能把 insight 作为高层 synthesized knowledge 注入，并保留 source ids 和 confidence。

#### Scenario: Search insight

- **WHEN** 用户搜索 insight 中的概念或自然语言语义
- **THEN** 系统返回 sourceType 为 `insight` 的结果

#### Scenario: Context includes insight

- **WHEN** context 查询命中高置信 insight
- **THEN** context evidence 包含该 insight 及其 source ids

### Requirement: Search Lifecycle Filtered Knowledge

系统 SHALL 在搜索和 context 中排除被 soft delete 的 lesson 或低置信 knowledge，除非用户显式请求宽召回。

Search and context MUST NOT 默认返回 `deleted=true` 的 lifecycle knowledge。系统 SHOULD 对低 confidence lifecycle knowledge 降权或过滤。用户显式指定 broad recall 时 MAY 返回低置信结果并保留 confidence。

#### Scenario: Hide deleted lesson

- **WHEN** lesson 被标记 deleted
- **THEN** 默认 search/context 不返回该 lesson

#### Scenario: Deprioritize low confidence knowledge

- **WHEN** knowledge confidence 低于默认阈值
- **THEN** search/context 降低其排序或过滤
