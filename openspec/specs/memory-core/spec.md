# memory-core Specification

## Purpose
TBD - created by archiving change add-memory-core. Update Purpose after archive.
## Requirements
### Requirement: Session Tracking

系统 SHALL 在 observation 写入时维护 session 状态，并 SHALL 支持显式 session start/end。

Session MUST 包含 `id`、`project`、`cwd`、`startedAt`、`updatedAt`、`observationCount`、`status`、`endedAt` 和 `summaryId`。`status` MUST 支持 `active` 和 `ended`。

#### Scenario: First observation creates session

- **WHEN** agent 写入某个 session 的第一条 observation
- **THEN** 系统创建 active session，并将 observationCount 设置为 1

#### Scenario: Later observation updates session

- **WHEN** agent 再次向同一 session 写入 observation
- **THEN** 系统更新 session 的 updatedAt，将 status 设为 active，并递增 observationCount

#### Scenario: Explicit session start creates session

- **WHEN** agent 显式 start 一个不存在的 session
- **THEN** 系统创建 active session，observationCount 为 0，且不写入 observation

#### Scenario: Explicit session start updates session

- **WHEN** agent 显式 start 一个已存在的 session
- **THEN** 系统更新 project、cwd、updatedAt 和 status，但不递增 observationCount

#### Scenario: Explicit session end creates session summary

- **WHEN** agent 显式 end 一个已有 session 且该 session 有 observations
- **THEN** 系统将 session 标记为 ended，设置 endedAt，生成会话级 summary，并把 session.summaryId 指向该 summary

#### Scenario: Session end without observations

- **WHEN** agent 显式 end 一个没有 observations 的 session
- **THEN** 系统将 session 标记为 ended 并设置 endedAt，但不生成 summary

### Requirement: Observation Save

系统 SHALL 保存 agent 工作过程 observation。

Observation MUST 包含 `id`、`sessionId`、`type`、`content`、`source`、`language`、`project`、`cwd`、`files`、`concepts` 和 `createdAt`。

Observation 保存成功后，系统 MUST 为 observation 创建 searchable document 并触发索引写入。索引写入失败 MUST NOT 回滚 observation 保存。

#### Scenario: Save observation

- **WHEN** agent 提交合法 observation payload
- **THEN** 系统保存 observation，并返回 observation id 和 session id

#### Scenario: Observation save triggers indexing

- **WHEN** 系统成功保存 observation
- **THEN** 系统为 observation 创建索引记录或记录 failed index job

### Requirement: Explicit Memory Save

系统 SHALL 保存用户明确要求保留的长期 memory。

Memory MUST 包含 `id`、`type`、`content`、`concepts`、`files`、`language`、`source` 和 `createdAt`。

Memory SHOULD 预留 `canonicalId`、`duplicateOf` 和 `relations` 字段，用于后续跨语言重复、补充、替代、冲突和相关关系治理。memory core 阶段 MUST NOT 自动合并跨语言相似 memory。

Memory 保存成功后，系统 MUST 为 memory 创建 searchable document 并触发索引写入。索引写入失败 MUST NOT 回滚 memory 保存。

#### Scenario: Save memory

- **WHEN** agent 提交合法 memory payload
- **THEN** 系统保存 memory，并返回 memory id

#### Scenario: Save multilingual duplicate candidate

- **WHEN** agent 保存一条与既有 memory 语义相近但语言不同的新 memory
- **THEN** memory core 保存新 memory，不自动删除或合并既有 memory

#### Scenario: Memory save triggers indexing

- **WHEN** 系统成功保存 memory
- **THEN** 系统为 memory 创建索引记录或记录 failed index job

### Requirement: Audit Writes

系统 MUST 为 observation 保存和 memory 保存写入 audit。

Audit 记录 MUST 包含 `id`、`action`、`targetType`、`targetId`、`source`、`timestamp` 和 `details`。

#### Scenario: Observation save writes audit

- **WHEN** 系统保存 observation
- **THEN** 系统写入 action 为 `observe` 的 audit 记录

#### Scenario: Memory save writes audit

- **WHEN** 系统保存 memory
- **THEN** 系统写入 action 为 `remember` 的 audit 记录

### Requirement: Core List Queries

系统 SHALL 支持列出 sessions、memories 和 audit。

#### Scenario: List sessions

- **WHEN** 客户端请求 session 列表
- **THEN** 系统返回已保存 sessions

#### Scenario: List memories

- **WHEN** 客户端请求 memory 列表
- **THEN** 系统返回已保存 memories

#### Scenario: List audit

- **WHEN** 客户端请求 audit 列表
- **THEN** 系统返回审计记录

### Requirement: Derived Memory Processing Data

系统 SHALL 支持列出 observation 派生的 summaries、session summaries、candidate memories 和 LLM processing jobs。

Summary 保存成功后，系统 MUST 为 summary 创建 searchable document 并触发索引写入。索引写入失败 MUST NOT 回滚 summary 保存或 LLM processing job 状态。Summary MUST 标明 `kind`，其中 `observation` 表示单条 observation 摘要，`session` 表示会话级 summary。

#### Scenario: List summaries

- **WHEN** 客户端请求 summary 列表
- **THEN** 系统返回已保存的 observation summaries 和 session summaries

#### Scenario: List candidate memories

- **WHEN** 客户端请求 candidate memory 列表
- **THEN** 系统返回已保存 candidate memories

#### Scenario: List LLM processing jobs

- **WHEN** 客户端请求 LLM processing job 列表
- **THEN** 系统返回已保存 processing jobs

#### Scenario: Summary save triggers indexing

- **WHEN** 系统成功保存 summary
- **THEN** 系统为 summary 创建索引记录或记录 failed index job

#### Scenario: Session summary is derived data

- **WHEN** 系统成功生成 session summary
- **THEN** summary.kind 为 `session`，summary.sessionId 指向对应 session

### Requirement: Wiki Core List Data

系统 SHALL 支持列出 Wiki pages 和 Wiki update jobs。

#### Scenario: List wiki pages from core

- **WHEN** 调用方请求 Wiki page 列表
- **THEN** core service 返回已保存 Wiki pages

#### Scenario: List wiki update jobs from core

- **WHEN** 调用方请求 Wiki update job 列表
- **THEN** core service 返回已保存 Wiki update jobs

