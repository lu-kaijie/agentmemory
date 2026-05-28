# python-service-foundation Specification

## Purpose
TBD - created by archiving change bootstrap-python-service. Update Purpose after archive.
## Requirements
### Requirement: Python Project Foundation

系统 SHALL 提供 Python 3.11+ 项目结构，并通过 `pyproject.toml` 声明运行依赖、开发依赖和 `agentmemory` CLI entry point。

#### Scenario: Project metadata exists

- **WHEN** 开发者查看项目根目录
- **THEN** 系统包含 `pyproject.toml`，并声明 Python 版本、包名、依赖和 CLI entry point

### Requirement: Configuration Loading

系统 SHALL 通过 Pydantic Settings 读取环境变量和 `.env` 配置。

配置 MUST 至少包含 host、port、database path、secret 和 log level。敏感值 MUST 在配置摘要和健康检查中隐藏。

#### Scenario: Default configuration loads

- **WHEN** 未设置环境变量时加载配置
- **THEN** 系统返回可用于本地开发的默认配置

#### Scenario: Secret is redacted

- **WHEN** 配置摘要包含 `AGENTMEMORY_SECRET`
- **THEN** 系统不返回 secret 明文

### Requirement: FastAPI Health Endpoints

系统 SHALL 提供 FastAPI 应用和健康检查端点。

P0 MUST 提供 `GET /agentmemory/livez` 和 `GET /agentmemory/health`。

#### Scenario: Livez endpoint returns alive

- **WHEN** 客户端请求 `/agentmemory/livez`
- **THEN** 系统返回 200 和 alive 状态

#### Scenario: Health endpoint reports database

- **WHEN** 客户端请求 `/agentmemory/health`
- **THEN** 系统返回服务名、版本、health 状态和数据库可用性

### Requirement: CLI Foundation

系统 SHALL 提供 `agentmemory` CLI。

P0 MUST 提供 `serve` 和 `doctor` 命令。

#### Scenario: Doctor command runs checks

- **WHEN** 开发者运行 `agentmemory doctor`
- **THEN** CLI 检查配置和数据库路径，并返回成功或失败结果

#### Scenario: Serve command starts API

- **WHEN** 开发者运行 `agentmemory serve`
- **THEN** CLI 使用配置的 host 和 port 启动 FastAPI 服务

