## ADDED Requirements

### Requirement: Project Interfaces
系统 SHALL 通过 CLI 和 REST 暴露 project 管理能力。

CLI MUST 提供 project list/show/update-profile 或等价命令。REST MUST 提供 project list/show/update-profile 或等价 endpoints。Profile update MUST 返回 Project Profile 和 source ids。

#### Scenario: CLI lists projects
- **WHEN** 用户运行 project list 命令
- **THEN** CLI 输出 ProjectRecord 列表

#### Scenario: REST updates project profile
- **WHEN** 客户端请求 profile update
- **THEN** API 返回更新后的 Project Profile

### Requirement: Pinned Memory Interfaces
系统 SHALL 通过 CLI 和 REST 暴露 pinned memory 管理能力。

CLI MUST 支持 pin、unpin/disable、list pinned items。REST MUST 提供等价 endpoints。所有接口 MUST 支持 global 和 project scope。

#### Scenario: CLI pins project memory
- **WHEN** 用户运行 pin 命令并指定 project
- **THEN** 系统创建 project pinned item

#### Scenario: REST lists pinned memory
- **WHEN** 客户端请求 pinned list
- **THEN** API 返回 global 和 project pinned items

## MODIFIED Requirements

### Requirement: Search REST API

系统 SHALL 通过 REST API 暴露 memory search 能力。

P0 MUST 提供：

- `POST /agentmemory/search`
- `POST /agentmemory/smart-search`

Search request MUST 支持 `query`、`mode`、`limit`、`project`、`projectId`、`scope`、`sessionId`、`language` 和 `sourceTypes`。Response MUST 返回结构化搜索结果和 source ids。

#### Scenario: REST keyword search

- **WHEN** 客户端向 `/agentmemory/search` 提交关键词 query
- **THEN** 系统返回匹配结果列表

#### Scenario: REST smart search

- **WHEN** 客户端向 `/agentmemory/smart-search` 提交自然语言 query
- **THEN** 系统返回 answer、results、evidence 和 context

### Requirement: Search CLI

系统 SHALL 通过 CLI 暴露 memory search 能力。

P0 MUST 提供：

- `agentmemory search`
- `agentmemory smart-search`

CLI MUST 支持 `--json`。CLI search MUST 支持 `--mode`、`--limit`、`--project`、`--project-id`、`--scope`、`--session-id`、`--language` 和 `--source-types`。

#### Scenario: CLI search json

- **WHEN** agent 运行 `agentmemory search "query" --json`
- **THEN** CLI 输出 JSON 格式的搜索结果

#### Scenario: CLI smart search json

- **WHEN** agent 运行 `agentmemory smart-search "query" --json`
- **THEN** CLI 输出 JSON 格式的 answer、results、evidence 和 context
