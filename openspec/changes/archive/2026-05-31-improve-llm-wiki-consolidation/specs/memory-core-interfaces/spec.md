## ADDED Requirements

### Requirement: LLM Wiki Consolidation Interfaces

系统 SHALL 通过 CLI 和 REST 暴露 LLM Wiki consolidation、lesson、crystal、reflect、lint 和 query filing 能力。

CLI MUST 提供 `agentmemory wiki consolidate --json`、`agentmemory wiki lessons --json`、`agentmemory wiki lesson-recall <query> --json`、`agentmemory wiki crystallize --source-ids <ids> --json`、`agentmemory wiki reflect --json`、`agentmemory wiki lint --json` 和 `agentmemory wiki file-answer --json`。REST MUST 提供对应 `/agentmemory/wiki/*` 端点。

#### Scenario: CLI consolidate wiki knowledge

- **WHEN** 用户运行 `agentmemory wiki consolidate --json`
- **THEN** CLI 返回 consolidation 摘要和创建或强化的 records

#### Scenario: REST lint wiki

- **WHEN** 客户端请求 `POST /agentmemory/wiki/lint`
- **THEN** REST 返回结构化 lint issues

#### Scenario: CLI file query answer

- **WHEN** 用户运行 `agentmemory wiki file-answer --query <query> --content <content> --json`
- **THEN** CLI 保存该 query answer 到 LLM Wiki 知识层

### Requirement: Maintenance Runs LLM Wiki Consolidation

系统 SHALL 允许 maintenance 入口调度 LLM Wiki consolidation。

Maintenance run MUST include wiki consolidation、lesson decay 和 optional reflect 摘要。系统 MUST 允许通过 request 或配置限制每轮处理数量，避免维护任务过度调用 LLM。

#### Scenario: Maintenance includes consolidation summary

- **WHEN** 用户运行 `agentmemory maintenance run --json`
- **THEN** 响应包含 wiki consolidation、lesson decay 或 reflect 的处理摘要

#### Scenario: Maintenance respects limit

- **WHEN** maintenance request 指定 limit
- **THEN** consolidation 和 reflect 每轮处理数量不超过 limit
