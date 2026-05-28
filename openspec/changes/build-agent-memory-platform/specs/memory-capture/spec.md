## ADDED Requirements

### Requirement: Observation Capture

系统 SHALL 接收 agent 会话事件和工具执行事件，并将它们保存为 observation。

每条 observation MUST 包含稳定的 `id`、`sessionId`、`timestamp`、`source`、`type` 和可搜索文本内容。系统 MUST 支持基础去重，避免同一事件被重复写入。

#### Scenario: Agent reports work observation

- **WHEN** agent 通过 CLI 或 REST API 提交一次工作过程 payload
- **THEN** 系统保存一条 observation，并把它关联到对应 session

#### Scenario: Duplicate observation is submitted

- **WHEN** 相同内容和相同 session 的 observation 被重复提交
- **THEN** 系统不会生成重复有效记录，并返回可追踪的处理结果

### Requirement: LLM Assisted Memory Extraction

系统 SHALL 从第一版开始使用 OpenAI-compatible LLM provider 对 observation 进行摘要和候选记忆提炼。

当 LLM provider 可用时，系统 MUST 为新 observation 或 session 生成可搜索摘要，并提炼候选 facts、decisions、files 和 lessons。当 LLM provider 不可用时，系统 MUST 保留原始 observation，并记录摘要任务的 pending 或 failed 状态。

#### Scenario: LLM extracts summary from observation

- **WHEN** 系统保存一条包含工具执行结果的 observation 且 LLM provider 可用
- **THEN** 系统生成摘要或候选记忆，并使其可被搜索命中

#### Scenario: LLM provider unavailable

- **WHEN** 系统保存 observation 时 LLM provider 不可用
- **THEN** observation 保存成功，摘要任务被标记为 pending 或 failed

### Requirement: Session Tracking

系统 SHALL 维护 session 元数据，包括 session id、项目路径、开始时间、结束时间、observation 数量和最后更新时间。

#### Scenario: First observation creates session

- **WHEN** 系统收到某个 `sessionId` 的第一条 observation
- **THEN** 系统创建对应 session，并更新 session 的统计信息

#### Scenario: Session end is recorded

- **WHEN** 系统收到 session end 事件
- **THEN** 系统记录结束时间，并保持该 session 的 observation 可搜索

### Requirement: Explicit Memory Save

系统 SHALL 允许用户显式保存长期 memory，并支持 `type`、`concepts`、`files` 和正文内容。

#### Scenario: User saves memory

- **WHEN** 用户通过 CLI 或 REST API 提交 memory 内容
- **THEN** 系统保存 memory，记录审计信息，并允许后续搜索命中

### Requirement: Audit On State Change

系统 MUST 对显式保存、删除、导入和导出等关键状态变更写入 audit 记录。

#### Scenario: Memory save writes audit

- **WHEN** 用户保存一条 memory
- **THEN** 系统写入包含操作类型、目标 id、时间戳和来源的 audit 记录
