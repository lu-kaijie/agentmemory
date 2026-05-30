## ADDED Requirements

### Requirement: Wiki Page Indexing

系统 SHALL 将 Wiki page 转换为 searchable document 并写入索引。

Wiki page searchable document MUST 使用 `sourceType=wikiPage`，`sourceId=<wikiPageId>`，并包含 title、topic、content 和 source ids 相关 searchable text。

#### Scenario: Index wiki page after update

- **WHEN** 系统成功创建或更新 Wiki page
- **THEN** 系统为 Wiki page 创建 searchable document 并触发索引写入

#### Scenario: Wiki index failure does not rollback page

- **WHEN** Wiki page 索引写入失败
- **THEN** 系统保留 Wiki page 并记录 failed index job

### Requirement: Distilled Knowledge Indexing

系统 SHALL 将 distilled knowledge 转换为 searchable document 并写入索引。

Distilled knowledge searchable document MUST 使用 `sourceType=knowledge`，`sourceId=<knowledgeId>`，并包含 kind、content、source ids、concepts 和 files 相关 searchable text。

#### Scenario: Index knowledge after distillation

- **WHEN** 系统成功创建 distilled knowledge
- **THEN** 系统为该 knowledge record 创建 searchable document 并触发索引写入

#### Scenario: Knowledge index failure does not rollback record

- **WHEN** distilled knowledge 索引写入失败
- **THEN** 系统保留 knowledge record 并记录 failed index job
