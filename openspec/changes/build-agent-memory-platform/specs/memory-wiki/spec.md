## ADDED Requirements

### Requirement: LLM Maintained Wiki Pages

系统 SHALL 使用 LLM 将碎片化 observation、summary 和 memory 沉淀为个人 Wiki 页面。

每个 Wiki 页面 MUST 包含稳定 id、title、topic、content、sourceIds、updatedAt 和 confidence。页面内容 MUST 保留来源引用，避免不可追溯的纯 LLM 结论。

#### Scenario: Wiki page is created from memories

- **WHEN** 系统收集到同一主题的 observation、summary 或 memory
- **THEN** LLM 生成或更新对应 Wiki 页面，并记录来源 id

#### Scenario: Wiki page remains traceable

- **WHEN** 用户查看 Wiki 页面
- **THEN** 系统展示页面内容和支撑该页面的来源记录

### Requirement: Wiki Update Review State

系统 SHALL 为 LLM 生成的 Wiki 更新记录状态，至少包括 `proposed`、`applied` 和 `failed`。

#### Scenario: LLM proposes wiki update

- **WHEN** 新 observation 触发 Wiki 更新
- **THEN** 系统保存更新建议或直接应用更新，并保留 audit 记录

### Requirement: Wiki Update Jobs

系统 SHALL 使用 Wiki 更新任务维护 Wiki 页面。

系统 MUST 在 observation、memory 或 summary 写入后创建 `wiki_update_job`。后台 worker MUST 处理 pending jobs，调用 LLM 生成结构化 update proposal，并在校验通过后应用到 Wiki 页面。失败任务 MUST 记录错误并可重试。

#### Scenario: Observation enqueues wiki update

- **WHEN** 系统保存新的 observation
- **THEN** 系统创建包含该 observation source id 的 Wiki 更新任务

#### Scenario: Worker applies wiki proposal

- **WHEN** worker 成功处理 Wiki 更新任务
- **THEN** 系统更新或创建 Wiki 页面，记录 sourceIds，并写入 audit

#### Scenario: Failed wiki job is retryable

- **WHEN** LLM 调用失败或 proposal 校验失败
- **THEN** 系统将任务标记为 failed，记录 lastError，并允许后续重试

### Requirement: Manual Wiki Rebuild

系统 SHALL 提供 CLI 和 REST 入口，用于手动更新或重建 Wiki 页面。

#### Scenario: User rebuilds one topic

- **WHEN** 用户调用 `agentmemory wiki rebuild --topic <topic>`
- **THEN** 系统根据该 topic 的相关 source ids 重新生成 Wiki 页面

#### Scenario: User rebuilds all wiki pages

- **WHEN** 用户调用全量 Wiki rebuild
- **THEN** 系统为所有 Wiki topic 创建重建任务

### Requirement: Wiki Search

系统 SHALL 允许 CLI、REST API 和 Viewer 搜索 Wiki 页面。

#### Scenario: Search returns wiki page

- **WHEN** 用户搜索某个长期主题
- **THEN** 系统返回相关 Wiki 页面，并包含页面摘要和来源引用
