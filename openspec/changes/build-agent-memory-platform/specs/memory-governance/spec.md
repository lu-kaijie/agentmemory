## ADDED Requirements

### Requirement: Export And Import

系统 SHALL 支持导出完整记忆数据为可迁移 JSON，并为后续导入保留版本字段。

#### Scenario: Export returns portable JSON

- **WHEN** 用户调用 `/agentmemory/export` 或 `memory_export`
- **THEN** 系统返回包含版本、sessions、observations、memories 和 audit 的 JSON

### Requirement: Governance Delete

系统 MUST 支持按 id 删除 memory 或 observation，并记录删除原因和审计条目。

#### Scenario: Delete memory with reason

- **WHEN** 用户请求删除某条 memory 并提供原因
- **THEN** 系统删除或标记该 memory，并写入包含原因的 audit 记录

### Requirement: Health Check

系统 SHALL 提供健康检查，报告 service、version、health、metrics、LLM provider 状态和 embedding provider 状态。

#### Scenario: Health endpoint available without secret

- **WHEN** 客户端访问 `/agentmemory/health`
- **THEN** 系统返回服务健康状态，不泄露敏感配置值

### Requirement: Configuration Flags

系统 SHALL 支持配置核心功能和高级功能开关。

P0 MUST 支持 `AGENTMEMORY_URL`、`AGENTMEMORY_SECRET`、`AGENTMEMORY_INJECT_CONTEXT`、`AGENTMEMORY_AUTO_COMPRESS`、`AGENTMEMORY_LLM_BASE_URL`、`AGENTMEMORY_LLM_MODEL`、`AGENTMEMORY_LLM_API_KEY`、`AGENTMEMORY_EMBEDDING_BASE_URL`、`AGENTMEMORY_EMBEDDING_MODEL`、`AGENTMEMORY_EMBEDDING_API_KEY`、`GRAPH_EXTRACTION_ENABLED` 和 `CONSOLIDATION_ENABLED`。

#### Scenario: Advanced feature disabled

- **WHEN** 图谱或 consolidation 配置关闭
- **THEN** 系统跳过对应后台任务，并保持核心保存和搜索功能可用
