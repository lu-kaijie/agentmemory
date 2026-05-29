## ADDED Requirements

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
