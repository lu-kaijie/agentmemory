## ADDED Requirements

### Requirement: Memory Core REST API

系统 SHALL 通过 REST API 暴露 memory core 能力。

P0 MUST 提供：

- `POST /agentmemory/observe`
- `POST /agentmemory/remember`
- `GET /agentmemory/sessions`
- `GET /agentmemory/memories`
- `GET /agentmemory/audit`

#### Scenario: REST observe

- **WHEN** 客户端向 `/agentmemory/observe` 提交合法 payload
- **THEN** 系统保存 observation 并返回 id

#### Scenario: REST remember

- **WHEN** 客户端向 `/agentmemory/remember` 提交合法 payload
- **THEN** 系统保存 memory 并返回 id

#### Scenario: REST list data

- **WHEN** 客户端请求 sessions、memories 或 audit
- **THEN** 系统返回对应列表

### Requirement: Memory Core CLI

系统 SHALL 通过 CLI 暴露 memory core 能力。

P0 MUST 提供：

- `agentmemory observe`
- `agentmemory remember`
- `agentmemory sessions`
- `agentmemory memories`
- `agentmemory audit`

CLI 查询命令 MUST 支持 `--json`。

#### Scenario: CLI observe

- **WHEN** agent 运行 `agentmemory observe --content <content>`
- **THEN** CLI 保存 observation 并输出结果

#### Scenario: CLI remember

- **WHEN** agent 运行 `agentmemory remember --content <content>`
- **THEN** CLI 保存 memory 并输出结果

#### Scenario: CLI list json

- **WHEN** agent 运行 `agentmemory memories --json`
- **THEN** CLI 输出 JSON 格式的 memory 列表
