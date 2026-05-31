## MODIFIED Requirements

### Requirement: Session Tracking

系统 SHALL 在 observation 写入时维护 session 状态，并 SHALL 支持显式 session start/end。

Session MUST 包含 `id`、`project`、`projectId`、`cwd`、`startedAt`、`updatedAt`、`observationCount`、`status`、`endedAt` 和 `summaryId`。`status` MUST 支持 `active` 和 `ended`。带 project/cwd 的 session start 或 observation MUST 创建或复用 ProjectRecord。

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
- **THEN** 系统更新 project、projectId、cwd、updatedAt 和 status，但不递增 observationCount

#### Scenario: Explicit session end creates session summary

- **WHEN** agent 显式 end 一个已有 session 且该 session 有 observations
- **THEN** 系统将 session 标记为 ended，设置 endedAt，生成会话级 summary，并把 session.summaryId 指向该 summary

#### Scenario: Session end without observations

- **WHEN** agent 显式 end 一个没有 observations 的 session
- **THEN** 系统将 session 标记为 ended 并设置 endedAt，但不生成 summary

## ADDED Requirements

### Requirement: Scoped Core Records
系统 SHALL 在 core records 中保留 scope/project identity。

Observation、memory、summary、knowledge、insight 和 wikiPage records MUST 支持 scope 和 projectId。Global records MUST 不要求 projectId。Project records MUST 绑定 ProjectRecord。

#### Scenario: Memory saved with project scope
- **WHEN** 用户在 project context 下保存 memory
- **THEN** memory 带有 scope=project 和 projectId

#### Scenario: Summary inherits session project
- **WHEN** session end 生成 summary
- **THEN** summary 继承 session 的 projectId
