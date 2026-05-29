## ADDED Requirements

### Requirement: Search REST API

系统 SHALL 通过 REST API 暴露 memory search 能力。

P0 MUST 提供：

- `POST /agentmemory/search`
- `POST /agentmemory/smart-search`

Search request MUST 支持 `query`、`mode`、`limit`、`project`、`language` 和 `sourceTypes`。Response MUST 返回结构化搜索结果和 source ids。

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

CLI MUST 支持 `--json`。CLI search MUST 支持 `--mode`、`--limit`、`--project`、`--language` 和 `--source-types`。

#### Scenario: CLI search json

- **WHEN** agent 运行 `agentmemory search "query" --json`
- **THEN** CLI 输出 JSON 格式的搜索结果

#### Scenario: CLI smart search json

- **WHEN** agent 运行 `agentmemory smart-search "query" --json`
- **THEN** CLI 输出 JSON 格式的 answer、results、evidence 和 context

### Requirement: Index REST API

系统 SHALL 通过 REST API 暴露 index 管理能力。

P0 MUST 提供：

- `GET /agentmemory/index/status`
- `POST /agentmemory/index/rebuild`
- `POST /agentmemory/index/repair`

#### Scenario: REST index status

- **WHEN** 客户端请求 `/agentmemory/index/status`
- **THEN** 系统返回索引状态摘要

#### Scenario: REST index rebuild

- **WHEN** 客户端请求 `/agentmemory/index/rebuild`
- **THEN** 系统重建索引并返回处理结果

#### Scenario: REST index repair

- **WHEN** 客户端请求 `/agentmemory/index/repair`
- **THEN** 系统修复缺失或失败的索引任务并返回处理结果

### Requirement: Index CLI

系统 SHALL 通过 CLI 暴露 index 管理能力。

P0 MUST 提供：

- `agentmemory index status`
- `agentmemory index rebuild`
- `agentmemory index repair`

CLI MUST 支持 `--json`。

#### Scenario: CLI index status

- **WHEN** agent 运行 `agentmemory index status --json`
- **THEN** CLI 输出 JSON 格式的索引状态
