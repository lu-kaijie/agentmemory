## ADDED Requirements

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
