# memory-indexing Specification

## Purpose

定义 AgentMemory 如何把 observation、memory 和 summary 转换为可检索文档，并维护 FTS5 关键词索引、LanceDB 向量索引和索引任务状态。

## Requirements

### Requirement: Search Document Indexing

系统 SHALL 将 observation、memory 和 summary 转换为 searchable document 并写入索引。

Search document MUST 包含 `id`、`sourceType`、`sourceId`、`sessionId`、`content`、`searchableText`、`language`、`project`、`files`、`concepts` 和 `createdAt`。

#### Scenario: Index observation after observe

- **WHEN** 系统保存 observation
- **THEN** 系统为 observation 创建 searchable document 并写入索引

#### Scenario: Index summary after LLM processing

- **WHEN** LLM processing 成功生成 summary
- **THEN** 系统为 summary 创建 searchable document 并写入索引

#### Scenario: Index memory after remember

- **WHEN** 系统保存 memory
- **THEN** 系统为 memory 创建 searchable document 并写入索引

### Requirement: FTS5 Index

系统 SHALL 使用 SQLite FTS5 保存 searchable document 的关键词索引。

FTS5 索引 MUST 支持按 source id 删除或重建记录。

#### Scenario: Keyword index is updated on write

- **WHEN** observation、memory 或 summary 写入成功
- **THEN** 对应 searchable document 可被 FTS5 检索

### Requirement: LanceDB Vector Index

系统 SHALL 使用 LanceDB 保存 searchable document 的 embedding 向量和 metadata。

向量记录 MUST 包含 source metadata，且 MUST 记录 embedding model 或 vector dimension 以支持后续 repair。

#### Scenario: Vector index is queued on write

- **WHEN** searchable document 写入索引
- **THEN** 系统创建 pending index job
- **AND** 写入请求不等待 embedding provider

### Requirement: Index Jobs

系统 SHALL 为 embedding/vector indexing 保存 index job 状态。

Index job MUST 包含 `id`、`type`、`targetType`、`targetId`、`status`、`attempts`、`lastError`、`startedAt` 和 `finishedAt`。Status MUST 支持 `pending`、`running`、`done` 和 `failed`。

#### Scenario: Indexing succeeds

- **WHEN** 后台 worker 或手动 repair/rebuild 生成 embedding 并写入 LanceDB 成功
- **THEN** 系统将 index job 标记为 `done`

#### Scenario: Indexing fails without losing source data

- **WHEN** 后台 worker 或手动 repair/rebuild 调用 embedding provider 或 LanceDB 写入失败
- **THEN** 系统保留原始 observation、memory 或 summary，并将 index job 标记为 `failed`

#### Scenario: Pending vector indexing does not block keyword search

- **WHEN** observation、memory 或 summary 写入成功
- **THEN** FTS5 关键词检索立即可用
- **AND** 向量检索可在 pending job 完成后可用

### Requirement: Index Status

系统 SHALL 提供 index status。

Index status MUST 返回已索引文档数、index job 数量、failed job 数量、FTS5 状态、LanceDB 状态和 embedding provider 状态。

#### Scenario: Report index status

- **WHEN** 客户端请求 index status
- **THEN** 系统返回 FTS5、LanceDB、jobs 和 provider 状态摘要

### Requirement: Index Rebuild And Repair

系统 SHALL 支持手动 rebuild 和 repair。

Rebuild MUST 清空并重建 FTS5 与 LanceDB 索引。Repair MUST 尝试补建缺失、pending 或 failed 的 index jobs。

#### Scenario: Rebuild all indexes

- **WHEN** 用户触发 index rebuild
- **THEN** 系统从已有 observation、memory 和 summary 重新生成索引

#### Scenario: Repair pending or failed index jobs

- **WHEN** 用户触发 index repair
- **THEN** 系统重试 pending、failed 或缺失的 index jobs
