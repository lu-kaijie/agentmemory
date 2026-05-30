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

### Requirement: Local Development Scripts

系统 SHALL 提供本地开发脚本、测试脚本和示例环境文件。

项目根目录 MUST 包含 `.env.example`，列出本地运行所需的 AgentMemory 配置项且不包含真实密钥。项目 MUST 提供 `scripts/dev.sh` 启动本地服务，提供 `scripts/test.sh` 运行测试和 OpenSpec 校验。

#### Scenario: Developer can discover local env

- **WHEN** 开发者查看项目根目录
- **THEN** `.env.example` 描述本地数据库、向量库、LLM 和 embedding 配置项

#### Scenario: Developer can run scripts

- **WHEN** 开发者运行本地脚本
- **THEN** 脚本使用 `uv run` 执行服务或测试命令

### Requirement: Maintenance Scheduler Configuration

系统 SHALL 提供后台维护调度配置。

配置 MUST 支持启用/关闭 maintenance worker、设置 interval seconds 和每轮 limit。配置摘要和 health MUST 展示维护调度配置，不返回敏感值。

#### Scenario: Maintenance config is visible

- **WHEN** 客户端请求 health
- **THEN** 响应包含 maintenance 配置摘要

