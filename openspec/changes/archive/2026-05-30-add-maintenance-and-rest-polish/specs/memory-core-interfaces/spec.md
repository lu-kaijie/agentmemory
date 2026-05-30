## ADDED Requirements

### Requirement: Maintenance Interfaces

系统 SHALL 通过 CLI 和 REST 暴露 maintenance 能力。

CLI MUST 提供 `agentmemory maintenance run --json`。REST MUST 提供 `POST /agentmemory/maintenance/run`。响应 MUST 包含 index、wiki、llm、pageCompression 和 errors 摘要。

#### Scenario: CLI maintenance run

- **WHEN** 用户运行 `agentmemory maintenance run --json`
- **THEN** CLI 输出维护处理摘要

#### Scenario: REST maintenance run

- **WHEN** 客户端请求 `POST /agentmemory/maintenance/run`
- **THEN** REST 返回维护处理摘要

### Requirement: Optional REST Response Envelope

系统 SHALL 支持可选统一 REST response envelope。

当配置启用或请求指定 envelope 时，REST response MUST 返回 `{ "status_code": <int>, "body": <payload>, "headers": <object> }`。默认情况下系统 MUST 保持现有裸 JSON 响应兼容。

#### Scenario: REST returns default JSON

- **WHEN** 未启用 envelope
- **THEN** REST 端点返回现有业务 JSON

#### Scenario: REST returns envelope

- **WHEN** 请求指定 envelope 或配置启用 envelope
- **THEN** REST 端点返回包含 status_code、body 和 headers 的统一 envelope
