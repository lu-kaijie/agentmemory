## MODIFIED Requirements

### Requirement: Wiki Update Jobs

系统 SHALL 保存 Wiki update job 状态。

Wiki update job MUST 包含 `id`、`sourceIds`、`topic`、`status`、`proposal`、`attempts`、`lastError`、`createdAt` 和 `updatedAt`。Status MUST 支持 `pending`、`running`、`applied` 和 `failed`。

#### Scenario: Enqueue wiki job from observation

- **WHEN** observation 保存成功
- **THEN** 系统创建 pending Wiki update job

#### Scenario: Enqueue wiki job from memory

- **WHEN** memory 保存成功
- **THEN** 系统创建 pending Wiki update job

#### Scenario: Enqueue wiki job from summary

- **WHEN** observation summary 或 session summary 保存成功
- **THEN** 系统创建 pending Wiki update job

### Requirement: Wiki Rebuild

系统 SHALL 支持手动重建 Wiki。

Rebuild MUST 支持指定 topic，也 MUST 支持 `all`。Rebuild MUST 基于已有 observations、memories、observation summaries 和 session summaries 创建 Wiki update jobs 并处理或返回处理结果。

Rebuild MUST 先收集现有 knowledge，识别缺失或过期 source coverage，再只对缺口 evidence 执行 distill。Wiki 页面生成 MUST 优先基于 distilled knowledge 聚合，而不是每次直接从全部原始 evidence 重复生成。

#### Scenario: Rebuild one topic

- **WHEN** 用户请求按 topic rebuild Wiki
- **THEN** 系统为该 topic 创建或处理 Wiki update job

#### Scenario: Rebuild all topics

- **WHEN** 用户请求 rebuild all Wiki topics
- **THEN** 系统为第一版固定 topic 集合创建或处理 Wiki update jobs

#### Scenario: Rebuild skips covered evidence

- **WHEN** source evidence 已有对应 distilled knowledge 且未过期
- **THEN** Wiki rebuild 复用该 knowledge，不重复创建新 knowledge

#### Scenario: Rebuild fills missing knowledge

- **WHEN** source evidence 没有对应 distilled knowledge
- **THEN** Wiki rebuild 为缺口 evidence 创建 knowledge 后再聚合页面
