## ADDED Requirements

### Requirement: Pinned Memory State
系统 SHALL 支持 pinned memory/slots。

Pinned item MUST 包含 id、scope、projectId、label、content、sourceIds、priority、confidence、enabled、createdAt 和 updatedAt。Pinned item MAY 引用已有 record，也 MAY 保存独立内容。Pinned item MUST 表达 context 注入优先级，而不是普通 memory type。

#### Scenario: Pin global memory
- **WHEN** 用户 pin 一个跨项目偏好或规则
- **THEN** 系统保存 enabled global pinned item

#### Scenario: Pin project memory
- **WHEN** 用户在 project 下 pin 一个项目约束
- **THEN** 系统保存 project pinned item 并绑定 projectId

### Requirement: Pinned Memory Management
系统 SHALL 提供创建、列表、启用、禁用和删除 pinned item 的接口。

CLI 和 REST MUST 支持 pin、unpin/list 或等价操作。Disabled pinned item MUST 不进入 context。

#### Scenario: Disable pinned item
- **WHEN** 用户禁用 pinned item
- **THEN** 后续 context 不包含该 pinned item

#### Scenario: List pinned items
- **WHEN** 用户请求 pinned list
- **THEN** 系统返回 global 和指定 project 的 pinned items

### Requirement: Pinned Context Priority
系统 SHALL 在 context 中优先展示 pinned items。

Global pinned items MUST 出现在 global section。Project pinned items MUST 出现在 project section。Pinned items MUST 保留 source ids 或注明无来源。

#### Scenario: Context prioritizes pinned memory
- **WHEN** context 同时有 pinned item 和普通 search evidence
- **THEN** pinned item 出现在普通 evidence 之前
