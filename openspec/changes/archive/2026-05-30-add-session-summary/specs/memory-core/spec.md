## MODIFIED Requirements

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
