# memory-wiki Specification

## Purpose

定义 AgentMemory 的 LLM Wiki 长期知识沉淀能力，包括 distilled knowledge、Wiki 页面、更新任务、审计和重建流程。
## Requirements
### Requirement: LLM Wiki Knowledge Layer Positioning

系统 SHALL 将 Wiki 页面视为 LLM Wiki 长期知识沉淀系统的第一阶段聚合视图。

第一版 Wiki 页面 MUST 支持从 observation、memory 和 summary evidence 生成可读页面。系统 SHOULD 保留后续扩展到 semantic facts、procedural patterns、lessons、crystals 和 reflect insights 的能力。固定 topic 页面 MUST NOT 被视为最终完整知识模型。

#### Scenario: Wiki page is an entry layer

- **WHEN** 系统从 evidence 创建或更新 Wiki 页面
- **THEN** 页面作为可读聚合入口保存 source ids、confidence 和内容

#### Scenario: Future distilled knowledge can feed wiki

- **WHEN** 后续系统引入 semantic facts、procedural patterns、lessons 或 crystals
- **THEN** Wiki rebuild SHOULD be able to use those distilled records as input evidence

### Requirement: Distilled Knowledge State

系统 SHALL 保存 LLM 从 evidence 中提炼的 distilled knowledge。

Distilled knowledge MUST 包含 `id`、`kind`、`content`、`sourceIds`、`concepts`、`files`、`confidence`、`createdAt` 和 `updatedAt`。`kind` MUST 支持 `semantic`、`procedural`、`lesson` 和 `crystal`。Distilled knowledge MUST 支持 `fingerprint`，用于基于 `kind`、normalized content 和 source group 去重。Lesson knowledge MUST 支持 `reinforcements` 和 `lastReinforcedAt`。Crystal knowledge MUST 支持稳定 source group 边界，避免同一 source group 重复生成近似 crystal。

#### Scenario: Create distilled knowledge from wiki job

- **WHEN** 系统处理 Wiki update job
- **THEN** 系统先使用 LLM 从 evidence 中提炼 distilled knowledge

#### Scenario: List distilled knowledge

- **WHEN** 客户端请求 distilled knowledge 列表
- **THEN** 系统返回已保存的 semantic、procedural、lesson 和 crystal records

#### Scenario: Distilled knowledge preserves provenance

- **WHEN** 系统保存 distilled knowledge
- **THEN** 记录保留 source ids、confidence 和审计记录

#### Scenario: Deduplicate exact distilled knowledge

- **WHEN** 新 distilled knowledge 与已有记录 fingerprint 相同
- **THEN** 系统更新已有记录的 source ids、updatedAt 和强化信息，而不是新增重复记录

#### Scenario: Stabilize crystal source group

- **WHEN** 同一 source group 已经存在 crystal
- **THEN** 系统复用或更新已有 crystal，而不是为每个 topic rebuild 创建近似 crystal

### Requirement: Distilled Knowledge Merge

系统 SHALL 在保存 distilled knowledge 前执行重复检测和保守合并。

系统 MUST 对 normalized content 计算 fingerprint。系统 SHOULD 对同 kind 的相似 knowledge 使用 embedding similarity 或 LLM 判断是否可合并；不能确定时 MUST 保留为独立记录并保留 source ids。合并 MUST NOT 删除 provenance。

#### Scenario: Merge repeated lesson

- **WHEN** 新 lesson 与已有 lesson 表达同一经验
- **THEN** 系统强化已有 lesson，增加 source ids 和 reinforcements

#### Scenario: Preserve uncertain similar records

- **WHEN** 两条 knowledge 相似但无法确定语义等价
- **THEN** 系统保留两条记录，避免误合并

### Requirement: Wiki Page State

系统 SHALL 保存 LLM 维护的 Wiki 页面。

Wiki page MUST 包含 `id`、`title`、`topic`、`content`、`sourceIds`、`confidence`、`createdAt` 和 `updatedAt`。Topic MUST 使用第一版固定 topic 集合：`personal_preferences`、`project_overview`、`technical_decisions`、`troubleshooting`、`files_and_modules`、`workflow_habits`。

#### Scenario: Create wiki page

- **WHEN** Wiki update proposal 指向一个不存在的 topic
- **THEN** 系统创建对应 Wiki 页面并保存 source ids

#### Scenario: Update wiki page

- **WHEN** Wiki update proposal 指向一个已存在的 topic
- **THEN** 系统更新该 Wiki 页面内容、confidence、updatedAt 和 source ids

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

### Requirement: Wiki LLM Processing

系统 SHALL 使用 LLM 基于 evidence、distilled knowledge 和现有 Wiki 页面生成 Wiki update proposal。

系统 MUST 只在 LLM 输出可解析的 Wiki update proposal 时应用更新。解析失败或 LLM 调用失败 MUST 将 job 标记为 `failed`，并保留原始 source 数据。

#### Scenario: Apply valid wiki proposal

- **WHEN** LLM 返回有效 Wiki update proposal
- **THEN** 系统应用 proposal 并将 job 标记为 `applied`

#### Scenario: Fail invalid wiki proposal

- **WHEN** LLM 返回不可解析的 Wiki update proposal
- **THEN** 系统不更新 Wiki 页面并将 job 标记为 `failed`

#### Scenario: LLM failure preserves source data

- **WHEN** Wiki LLM processing 失败
- **THEN** observation、memory 或 summary 原始数据保持可读取

### Requirement: Wiki Audit

系统 MUST 为 Wiki 页面创建或更新写入 audit。

Wiki audit MUST 使用 action `wiki_update`，targetType `wiki_page`，targetId 为 Wiki page id，并记录 job id、topic 和 source ids。

#### Scenario: Wiki update writes audit

- **WHEN** 系统成功创建或更新 Wiki 页面
- **THEN** 系统写入 action 为 `wiki_update` 的 audit 记录

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

### Requirement: Wiki List Queries

系统 SHALL 支持列出 Wiki pages 和 Wiki update jobs。

#### Scenario: List wiki pages

- **WHEN** 客户端请求 Wiki page 列表
- **THEN** 系统返回已保存 Wiki pages

#### Scenario: List wiki jobs

- **WHEN** 客户端请求 Wiki update job 列表
- **THEN** 系统返回已保存 Wiki update jobs

