# memory-core-interfaces Specification

## Purpose
TBD - created by archiving change add-memory-core. Update Purpose after archive.
## Requirements
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

### Requirement: Provider Status In Health API

系统 SHALL 在 `/agentmemory/health` 中报告 LLM 与 embedding provider 的配置状态。

响应 MUST 包含 provider 名称、模型名、是否已配置密钥、是否就绪和最近错误。响应 MUST NOT 返回 API key 明文。

#### Scenario: Health reports configured providers

- **WHEN** 系统已配置 LLM 与 embedding provider
- **THEN** health 响应显示 LLM 与 embedding provider 为 openai-compatible 且就绪

#### Scenario: Health redacts provider secrets

- **WHEN** 系统配置了 LLM 或 embedding API key
- **THEN** health 响应只显示密钥是否已配置，不显示密钥内容

### Requirement: Provider Status In Doctor CLI

系统 SHALL 在 `agentmemory doctor` 中报告 LLM 与 embedding provider 的配置状态。

Doctor 输出 MUST 显示 provider 名称、模型名、是否已配置密钥和是否就绪。Doctor 输出 MUST NOT 显示 API key 明文。

#### Scenario: Doctor reports provider status

- **WHEN** 用户运行 `agentmemory doctor`
- **THEN** CLI 输出 LLM 与 embedding provider 状态

### Requirement: Derived Memory Processing REST API

系统 SHALL 通过 REST API 暴露 LLM memory processing 派生数据。

P0 MUST 提供：

- `GET /agentmemory/summaries`
- `GET /agentmemory/memory-candidates`
- `GET /agentmemory/llm-processing-jobs`

#### Scenario: REST list processing data

- **WHEN** 客户端请求 summaries、memory candidates 或 LLM processing jobs
- **THEN** 系统返回对应列表

### Requirement: Derived Memory Processing CLI

系统 SHALL 通过 CLI 暴露 LLM memory processing 派生数据。

P0 MUST 提供：

- `agentmemory summaries`
- `agentmemory memory-candidates`
- `agentmemory llm-processing-jobs`

CLI 查询命令 MUST 支持 `--json`。

#### Scenario: CLI list processing data json

- **WHEN** agent 运行 `agentmemory summaries --json`
- **THEN** CLI 输出 JSON 格式的 summary 列表
