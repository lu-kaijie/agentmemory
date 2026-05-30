## ADDED Requirements

### Requirement: Viewer Wiki Pages

Viewer SHALL 提供只读 Wiki page 列表。

Viewer MUST 通过 `/agentmemory/wiki/pages` 获取 Wiki 页面数据，并展示 title、topic、content、sourceIds、confidence 和 updatedAt。

#### Scenario: Browse wiki pages

- **WHEN** 用户打开 Viewer 的 Wiki 页面视图
- **THEN** Viewer 展示已保存 Wiki pages

### Requirement: Viewer Wiki Jobs

Viewer SHALL 提供只读 Wiki update job 列表。

Viewer MUST 通过 `/agentmemory/wiki/jobs` 获取 Wiki job 数据，并展示 job id、topic、status、sourceIds、attempts、lastError 和 updatedAt。

#### Scenario: Browse wiki jobs

- **WHEN** 用户打开 Viewer 的 Wiki jobs 视图
- **THEN** Viewer 展示已保存 Wiki update jobs

### Requirement: Viewer Distilled Knowledge

Viewer SHALL 提供只读 distilled knowledge 列表。

Viewer MUST 通过 `/agentmemory/wiki/knowledge` 获取 distilled knowledge 数据，并展示 kind、content、sourceIds、concepts、files、confidence 和 updatedAt。

#### Scenario: Browse distilled knowledge

- **WHEN** 用户打开 Viewer 的 Knowledge 视图
- **THEN** Viewer 展示已保存 semantic、procedural、lesson 和 crystal records

### Requirement: Viewer Remains Read Only For Wiki

Viewer SHALL 保持 Wiki 只读。

Viewer MUST NOT 提供 Wiki 编辑、删除、手动应用 proposal、Hook、MCP 或权限管理入口。

#### Scenario: Viewer does not expose wiki mutations

- **WHEN** 用户打开 Viewer
- **THEN** 页面不展示 Wiki 编辑或删除操作
