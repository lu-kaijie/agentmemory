## ADDED Requirements

### Requirement: Provider Status In Health API

系统 SHALL 在 `/agentmemory/health` 中报告 LLM 与 embedding provider 的配置状态。

响应 MUST 包含 provider 名称、模型名、是否已配置密钥、是否就绪和最近错误。响应 MUST NOT 返回 API key 明文。

#### Scenario: Health reports fake providers

- **WHEN** 系统使用默认 fake providers
- **THEN** health 响应显示 LLM 与 embedding provider 为 fake 且就绪

#### Scenario: Health redacts provider secrets

- **WHEN** 系统配置了 LLM 或 embedding API key
- **THEN** health 响应只显示密钥是否已配置，不显示密钥内容

### Requirement: Provider Status In Doctor CLI

系统 SHALL 在 `agentmemory doctor` 中报告 LLM 与 embedding provider 的配置状态。

Doctor 输出 MUST 显示 provider 名称、模型名、是否已配置密钥和是否就绪。Doctor 输出 MUST NOT 显示 API key 明文。

#### Scenario: Doctor reports provider status

- **WHEN** 用户运行 `agentmemory doctor`
- **THEN** CLI 输出 LLM 与 embedding provider 状态
