## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Distilled Knowledge Merge

系统 SHALL 在保存 distilled knowledge 前执行重复检测和保守合并。

系统 MUST 对 normalized content 计算 fingerprint。系统 SHOULD 对同 kind 的相似 knowledge 使用 embedding similarity 或 LLM 判断是否可合并；不能确定时 MUST 保留为独立记录并保留 source ids。合并 MUST NOT 删除 provenance。

#### Scenario: Merge repeated lesson

- **WHEN** 新 lesson 与已有 lesson 表达同一经验
- **THEN** 系统强化已有 lesson，增加 source ids 和 reinforcements

#### Scenario: Preserve uncertain similar records

- **WHEN** 两条 knowledge 相似但无法确定语义等价
- **THEN** 系统保留两条记录，避免误合并

### Requirement: Wiki Rebuild Reuses Knowledge

系统 SHALL 在 Wiki rebuild 时优先复用已有 distilled knowledge。

Rebuild MUST 先收集现有 knowledge，识别缺失或过期 source coverage，再只对缺口 evidence 执行 distill。Wiki 页面生成 MUST 优先基于 distilled knowledge 聚合，而不是每次直接从全部原始 evidence 重复生成。

#### Scenario: Rebuild skips covered evidence

- **WHEN** source evidence 已有对应 distilled knowledge 且未过期
- **THEN** Wiki rebuild 复用该 knowledge，不重复创建新 knowledge

#### Scenario: Rebuild fills missing knowledge

- **WHEN** source evidence 没有对应 distilled knowledge
- **THEN** Wiki rebuild 为缺口 evidence 创建 knowledge 后再聚合页面
