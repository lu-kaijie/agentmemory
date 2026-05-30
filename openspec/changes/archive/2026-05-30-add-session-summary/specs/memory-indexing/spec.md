## MODIFIED Requirements

### Requirement: Search Document Indexing

系统 SHALL 将 observation、memory、observation summary 和 session summary 转换为 searchable document 并写入索引。

Search document MUST 包含 `id`、`sourceType`、`sourceId`、`sessionId`、`content`、`searchableText`、`language`、`project`、`files`、`concepts` 和 `createdAt`。

#### Scenario: Index observation after observe

- **WHEN** 系统保存 observation
- **THEN** 系统为 observation 创建 searchable document 并写入索引

#### Scenario: Index summary after LLM processing

- **WHEN** LLM processing 成功生成 observation summary
- **THEN** 系统为 summary 创建 searchable document 并写入索引

#### Scenario: Index session summary after session end

- **WHEN** 系统成功生成 session summary
- **THEN** 系统为 summary 创建 searchable document 并写入索引

#### Scenario: Index memory after remember

- **WHEN** 系统保存 memory
- **THEN** 系统为 memory 创建 searchable document 并写入索引

### Requirement: Index Rebuild And Repair

系统 SHALL 支持手动 rebuild 和 repair。

Rebuild MUST 清空并重建 FTS5 与 LanceDB 索引。Repair MUST 尝试补建缺失、pending 或 failed 的 index jobs。

#### Scenario: Rebuild all indexes

- **WHEN** 用户触发 index rebuild
- **THEN** 系统从已有 observation、memory、observation summary 和 session summary 重新生成索引

#### Scenario: Repair pending or failed index jobs

- **WHEN** 用户触发 index repair
- **THEN** 系统重试 pending、failed 或缺失的 index jobs
