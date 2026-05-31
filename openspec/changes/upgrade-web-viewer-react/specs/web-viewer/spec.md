## MODIFIED Requirements

### Requirement: Viewer Entry

系统 SHALL 通过 `agentmemory serve` 托管 Web Viewer。

Viewer 入口 MUST 为 `/agentmemory/`。访问该路径 MUST 返回 Vite + React 构建的 Viewer HTML 页面。Viewer 静态资源 MUST 通过 `/agentmemory/assets/*` 托管。

#### Scenario: Open React viewer

- **WHEN** 用户访问 `/agentmemory/`
- **THEN** 系统返回包含 Viewer root 和 module asset 的 HTML 页面

### Requirement: Status Dashboard

Viewer SHALL 展示服务健康状态、LLM provider 状态、embedding provider 状态、search index 状态和当前数据库路径。

状态数据 MUST 来自现有 REST API，不得在 Viewer 中伪造状态。

#### Scenario: Show service status

- **WHEN** Viewer 加载
- **THEN** 页面展示 health、provider、index status 和维护状态摘要

### Requirement: Memory Data Lists

Viewer SHALL 提供只读列表查看 projects、pinned memory、sessions、memories、summaries、memory candidates、audit、LLM processing jobs、Wiki pages、Wiki jobs 和 distilled knowledge。

列表 MUST 显示每条记录的核心字段、id、scope、project/projectId、sourceIds 和 updatedAt/createdAt。Viewer MUST NOT 修改这些数据。

#### Scenario: Browse scoped records

- **WHEN** 用户选择 Global、Project 或 All scope
- **THEN** Viewer 按 scope 和 selected project 过滤对应 REST API 返回的记录

### Requirement: Search Interface

Viewer SHALL 提供 search、smart-search 和 context 交互。

Search MUST 支持 `keyword`、`vector` 和 `hybrid` mode。Smart-search MUST 展示 answer、results、evidence 和 context。Context MUST 展示 fixed sections，包括 identity、global、project、wiki-synthesis、lessons-and-crystals、recent-evidence 和 evidence。

#### Scenario: Run context

- **WHEN** 用户输入 query 并执行 context
- **THEN** Viewer 调用 `/agentmemory/context` 并按 sections 展示上下文

### Requirement: Lightweight Relationship Graph

Viewer SHALL 使用 React Flow 提供轻量关系图视图。

关系图 MUST 基于现有 records 的 project、session、file、concept、memory、summary、Wiki page、knowledge 和 pinned memory 信息派生。第一版关系图 MUST NOT 依赖独立持久化 graphNodes/graphEdges。

#### Scenario: Show derived relationship graph

- **WHEN** Viewer 已加载 records
- **THEN** 页面展示可缩放、可拖拽的关系图

### Requirement: Read-Only Viewer

Viewer SHALL 保持只读。

Viewer MUST NOT 提供编辑、删除、导入、导出、候选记忆转正、Hook、MCP、Wiki 页面维护或权限管理入口。

#### Scenario: Viewer does not expose unsupported actions

- **WHEN** 用户打开 Viewer
- **THEN** 页面不展示当前版本未实现或不在范围内的 mutation 操作入口
