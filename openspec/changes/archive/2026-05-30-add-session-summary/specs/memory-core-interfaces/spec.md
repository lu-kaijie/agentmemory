## ADDED Requirements

### Requirement: Session Lifecycle REST API

系统 SHALL 通过 REST API 暴露 session lifecycle 能力。

API MUST 提供 `POST /agentmemory/session/start` 和 `POST /agentmemory/session/end`。Start request MUST 支持可选 `sessionId`、`project`、`cwd` 和 `source`。End request MUST 支持 `sessionId`、可选 `content`、`language`、`project`、`cwd` 和 `source`。

#### Scenario: REST session start

- **WHEN** 客户端向 `/agentmemory/session/start` 提交合法 payload
- **THEN** 系统创建或更新 active session 并返回 session

#### Scenario: REST session end

- **WHEN** 客户端向 `/agentmemory/session/end` 提交合法 payload
- **THEN** 系统结束 session 并返回 session 与可选 session summary

### Requirement: Session Lifecycle CLI

系统 SHALL 通过 CLI 暴露 session lifecycle 能力。

CLI MUST 提供 `agentmemory session start` 和 `agentmemory session end`。两个命令 MUST 支持 `--json`。

#### Scenario: CLI session start

- **WHEN** agent 运行 `agentmemory session start --json`
- **THEN** CLI 输出创建或更新后的 session JSON

#### Scenario: CLI session end

- **WHEN** agent 运行 `agentmemory session end --session-id <id> --json`
- **THEN** CLI 输出结束后的 session JSON 和可选 session summary
