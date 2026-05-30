## ADDED Requirements

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
