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

### Requirement: Search REST API

系统 SHALL 通过 REST API 暴露 memory search 能力。

P0 MUST 提供：

- `POST /agentmemory/search`
- `POST /agentmemory/smart-search`

Search request MUST 支持 `query`、`mode`、`limit`、`project`、`language` 和 `sourceTypes`。Response MUST 返回结构化搜索结果和 source ids。

#### Scenario: REST keyword search

- **WHEN** 客户端向 `/agentmemory/search` 提交关键词 query
- **THEN** 系统返回匹配结果列表

#### Scenario: REST smart search

- **WHEN** 客户端向 `/agentmemory/smart-search` 提交自然语言 query
- **THEN** 系统返回 answer、results、evidence 和 context

### Requirement: Search CLI

系统 SHALL 通过 CLI 暴露 memory search 能力。

P0 MUST 提供：

- `agentmemory search`
- `agentmemory smart-search`

CLI MUST 支持 `--json`。CLI search MUST 支持 `--mode`、`--limit`、`--project`、`--language` 和 `--source-types`。

#### Scenario: CLI search json

- **WHEN** agent 运行 `agentmemory search "query" --json`
- **THEN** CLI 输出 JSON 格式的搜索结果

#### Scenario: CLI smart search json

- **WHEN** agent 运行 `agentmemory smart-search "query" --json`
- **THEN** CLI 输出 JSON 格式的 answer、results、evidence 和 context

### Requirement: Index REST API

系统 SHALL 通过 REST API 暴露 index 管理能力。

P0 MUST 提供：

- `GET /agentmemory/index/status`
- `POST /agentmemory/index/rebuild`
- `POST /agentmemory/index/repair`

#### Scenario: REST index status

- **WHEN** 客户端请求 `/agentmemory/index/status`
- **THEN** 系统返回索引状态摘要

#### Scenario: REST index rebuild

- **WHEN** 客户端请求 `/agentmemory/index/rebuild`
- **THEN** 系统重建索引并返回处理结果

#### Scenario: REST index repair

- **WHEN** 客户端请求 `/agentmemory/index/repair`
- **THEN** 系统修复缺失或失败的索引任务并返回处理结果

### Requirement: Index CLI

系统 SHALL 通过 CLI 暴露 index 管理能力。

P0 MUST 提供：

- `agentmemory index status`
- `agentmemory index rebuild`
- `agentmemory index repair`

CLI MUST 支持 `--json`。

#### Scenario: CLI index status

- **WHEN** agent 运行 `agentmemory index status --json`
- **THEN** CLI 输出 JSON 格式的索引状态

### Requirement: Skill-Compatible CLI Output

系统 SHALL 保持 AgentMemory CLI 适合 Skill 驱动的 agent 调用。

查询类 CLI 命令 MUST 支持 `--json`，写入类 CLI 命令 SHOULD 提供可解析的成功标识。Skill MUST 以当前已实现 CLI 命令为准，不引用未实现命令。

#### Scenario: Agent parses query output

- **WHEN** agent 按 Skill 调用查询类 CLI 命令并传入 `--json`
- **THEN** CLI 返回结构化 JSON

### Requirement: Skill-Compatible REST Fallback

系统 SHALL 保持 REST API 可作为 Skill 的兜底调用入口。

Skill 中列出的 REST 路径 MUST 对应当前已实现接口。REST 响应 MUST 包含 agent 可追踪的 source ids、job ids 或实体 ids。

#### Scenario: Agent falls back to REST API

- **WHEN** agent 无法使用 CLI 但可以调用本地 HTTP 服务
- **THEN** agent 可以按 Skill 调用 REST API 完成等价操作

### Requirement: Viewer Static Entry

系统 SHALL 通过 REST 服务暴露 Web Viewer 静态入口。

`GET /agentmemory/` MUST 返回 Viewer HTML。该入口 MUST 与现有 API 路径共存，不得破坏 `/agentmemory/health`、`/agentmemory/search` 等接口。

#### Scenario: Viewer route coexists with API routes

- **WHEN** 用户访问 `/agentmemory/`
- **THEN** 系统返回 Viewer HTML
- **AND** 现有 `/agentmemory/health` API 仍可正常返回 JSON

### Requirement: Viewer Uses Existing API

Viewer SHALL 使用现有 REST API 获取状态、数据列表、搜索结果和索引状态。

如果实现需要新增 Viewer 专用 endpoint，该 endpoint MUST 只读，且 MUST NOT 绕过 core service 或 StateKV 抽象。

#### Scenario: Viewer fetches API data

- **WHEN** Viewer 加载数据
- **THEN** Viewer 通过 REST API 获取数据，而不是直接读取本地数据库
