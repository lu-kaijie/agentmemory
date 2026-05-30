## ADDED Requirements

### Requirement: Wiki REST API

系统 SHALL 通过 REST API 暴露 Wiki 能力。

P0 MUST 提供：

- `GET /agentmemory/wiki/pages`
- `GET /agentmemory/wiki/jobs`
- `GET /agentmemory/wiki/knowledge`
- `POST /agentmemory/wiki/update`
- `POST /agentmemory/wiki/rebuild`

#### Scenario: REST list wiki pages

- **WHEN** 客户端请求 `/agentmemory/wiki/pages`
- **THEN** 系统返回 Wiki page 列表

#### Scenario: REST list wiki jobs

- **WHEN** 客户端请求 `/agentmemory/wiki/jobs`
- **THEN** 系统返回 Wiki update job 列表

#### Scenario: REST list wiki knowledge

- **WHEN** 客户端请求 `/agentmemory/wiki/knowledge`
- **THEN** 系统返回 distilled knowledge 列表

#### Scenario: REST update wiki jobs

- **WHEN** 客户端请求 `/agentmemory/wiki/update`
- **THEN** 系统处理 pending Wiki update jobs 并返回处理结果

#### Scenario: REST rebuild wiki

- **WHEN** 客户端请求 `/agentmemory/wiki/rebuild`
- **THEN** 系统按 topic 或 all 创建并处理 Wiki update jobs

### Requirement: Wiki CLI

系统 SHALL 通过 CLI 暴露 Wiki 能力。

P0 MUST 提供：

- `agentmemory wiki pages`
- `agentmemory wiki jobs`
- `agentmemory wiki knowledge`
- `agentmemory wiki update`
- `agentmemory wiki rebuild --topic <topic>`
- `agentmemory wiki rebuild --all`

查询类 Wiki CLI MUST 支持 `--json`。

#### Scenario: CLI list wiki pages

- **WHEN** 用户运行 `agentmemory wiki pages --json`
- **THEN** CLI 输出 JSON 格式的 Wiki page 列表

#### Scenario: CLI list wiki jobs

- **WHEN** 用户运行 `agentmemory wiki jobs --json`
- **THEN** CLI 输出 JSON 格式的 Wiki update job 列表

#### Scenario: CLI list wiki knowledge

- **WHEN** 用户运行 `agentmemory wiki knowledge --json`
- **THEN** CLI 输出 JSON 格式的 distilled knowledge 列表

#### Scenario: CLI update wiki

- **WHEN** 用户运行 `agentmemory wiki update --json`
- **THEN** CLI 处理 pending Wiki update jobs 并输出 JSON 结果

#### Scenario: CLI rebuild wiki

- **WHEN** 用户运行 `agentmemory wiki rebuild --all --json`
- **THEN** CLI 创建或处理 Wiki rebuild jobs 并输出 JSON 结果
