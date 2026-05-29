## ADDED Requirements

### Requirement: Viewer Entry

系统 SHALL 通过 `agentmemory serve` 托管 Web Viewer。

Viewer 入口 MUST 为 `/agentmemory/`。访问该路径 MUST 返回可在浏览器打开的 HTML 页面。

#### Scenario: Open viewer

- **WHEN** 用户访问 `/agentmemory/`
- **THEN** 系统返回 Web Viewer 页面

### Requirement: Status Dashboard

Viewer SHALL 展示服务健康状态、LLM provider 状态、embedding provider 状态和 search index 状态。

状态数据 MUST 来自现有 REST API，不得在 Viewer 中伪造状态。

#### Scenario: Show service status

- **WHEN** Viewer 加载
- **THEN** 页面展示 health、provider 和 index status 摘要

### Requirement: Memory Data Lists

Viewer SHALL 提供只读列表查看 sessions、memories、summaries、memory candidates、audit 和 LLM processing jobs。

列表 MUST 显示每条记录的核心字段和 id。Viewer MUST NOT 修改这些数据。

#### Scenario: Browse memory records

- **WHEN** 用户打开数据列表
- **THEN** Viewer 展示对应 REST API 返回的记录

### Requirement: Search Interface

Viewer SHALL 提供 search 和 smart-search 交互。

Search MUST 支持 `keyword`、`vector` 和 `hybrid` mode。Smart-search MUST 展示 answer、results、evidence 和 context。

#### Scenario: Run search

- **WHEN** 用户输入 query 并执行 search
- **THEN** Viewer 调用 `/agentmemory/search` 并展示 results

#### Scenario: Run smart search

- **WHEN** 用户输入 query 并执行 smart-search
- **THEN** Viewer 调用 `/agentmemory/smart-search` 并展示 answer、evidence、results 和 context

### Requirement: Lightweight Relationship Graph

Viewer SHALL 提供轻量关系图视图。

关系图 MUST 基于现有 records 的 session、project、file、concept、memory 和 summary 信息派生。第一版关系图 MUST NOT 依赖独立持久化 graphNodes/graphEdges。

#### Scenario: Show derived relationship graph

- **WHEN** Viewer 已加载 memory 和 session 数据
- **THEN** 页面展示由已有数据派生的节点和边

### Requirement: Read-Only Viewer

Viewer SHALL 保持只读。

Viewer MUST NOT 提供编辑、删除、导入、导出、候选记忆转正、Hook、MCP、Wiki 页面维护或权限管理入口。

#### Scenario: Viewer does not expose unsupported actions

- **WHEN** 用户打开 Viewer
- **THEN** 页面不展示当前版本未实现或不在范围内的操作入口
