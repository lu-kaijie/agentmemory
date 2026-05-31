## ADDED Requirements

### Requirement: LLM Wiki Consolidation

系统 SHALL 支持对长期 evidence 和 distilled knowledge 执行 LLM Wiki consolidation。

Consolidation MUST 从 session summaries、memories 和已有 knowledge 中提炼更稳定的 semantic 和 procedural knowledge。系统 MUST 使用 source ids、confidence 和 fingerprint 避免重复沉淀。系统 MUST 支持最小证据数量或置信阈值，避免把一次性细节过早固化为稳定知识。Consolidation MUST 让 LLM 读取 evidence 和已有 Wiki records 后判断稳定事实、可复用流程、冲突、陈旧结论和需要合并的记录。LLM provider 不可用时，系统 MUST 返回明确错误，而不是用关键词规则生成替代 consolidation。

#### Scenario: Consolidate stable semantic facts

- **WHEN** 多条 summary、memory 或 knowledge 支撑同一稳定事实
- **THEN** 系统创建或强化 semantic knowledge，并保留 source ids

#### Scenario: Consolidate recurring procedures

- **WHEN** 多条 evidence 表达重复工作流或操作模式
- **THEN** 系统创建或强化 procedural knowledge

#### Scenario: Skip insufficient evidence

- **WHEN** evidence 数量或置信不足
- **THEN** consolidation 不创建稳定 knowledge 或只返回 skipped 摘要

#### Scenario: LLM consolidates evidence with existing records

- **WHEN** LLM provider 可用且 evidence 达到最小数量
- **THEN** 系统把 evidence、已有 knowledge、insights 和 Wiki pages 交给 LLM，并保存 LLM 返回的 semantic/procedural/lesson/crystal knowledge

### Requirement: Dynamic Wiki Pages

系统 SHALL 支持由 LLM consolidation 生成动态 Wiki pages。

固定 Wiki topics MUST 继续作为导航入口和兼容层。系统 MUST 支持 `topic`、`entity`、`concept`、`source`、`comparison` 和 `synthesis` 页面类型。动态页面 MUST 包含 title、type、slug、parent topic、content、sourceIds、confidence、createdAt 和 updatedAt。系统 MUST 使用 type+slug 复用或更新已有动态页面，而不是重复创建同名页面。动态页面 MUST 进入 search/context 索引。

#### Scenario: Create concept page

- **WHEN** LLM consolidation 返回 `type=concept` 的 page
- **THEN** 系统保存动态 concept page，并用 slug 支持后续更新

#### Scenario: Search dynamic page

- **WHEN** 用户搜索动态页面 title、slug、type 或 content
- **THEN** search/context 可返回对应 wikiPage document

### Requirement: Lesson Lifecycle

系统 SHALL 为 lesson knowledge 提供生命周期管理。

Lesson MUST 支持 recall、strengthen、decay 和 soft delete。Lesson MUST 保留 confidence、reinforcements、lastReinforcedAt、decayRate、lastDecayedAt、deleted、sourceIds 和 project。重复 lesson MUST 强化已有记录而不是新增重复记录。Decay MUST NOT 物理删除 lesson。

#### Scenario: Recall lessons

- **WHEN** 用户按 query 检索 lessons
- **THEN** 系统返回未删除且满足最小 confidence 的 lesson results

#### Scenario: Strengthen repeated lesson

- **WHEN** 新 lesson 与已有 lesson 表达同一经验
- **THEN** 系统增加 reinforcements、更新 lastReinforcedAt 并提高 confidence

#### Scenario: Decay old lesson

- **WHEN** lesson 长时间未被强化或访问
- **THEN** 系统降低 confidence，并在低置信且未强化时标记 deleted

### Requirement: Crystal Lifecycle

系统 SHALL 支持从一组 evidence 生成阶段性 crystal。

Crystal MUST 表达一组 source evidence 的 compact digest，包含 narrative、key outcomes、files、concepts、lessons、sourceIds、sourceGroup、confidence 和 timestamps。系统 MUST 对同一 sourceGroup 复用或更新已有 crystal，避免重复生成近似 digest。Crystal 中提取出的 lessons SHOULD 强化 lesson knowledge。

#### Scenario: Create crystal from source group

- **WHEN** 用户或 maintenance 请求对一组 source ids crystallize
- **THEN** 系统保存 crystal knowledge 并保留 source group

#### Scenario: Reuse existing crystal

- **WHEN** 同一 source group 已有 crystal
- **THEN** 系统复用或更新已有 crystal，而不是创建重复 crystal

#### Scenario: Crystal strengthens lessons

- **WHEN** crystal 输出包含 lessons
- **THEN** 系统创建或强化对应 lesson records

### Requirement: Reflect Insights

系统 SHALL 支持从 semantic、procedural、lesson 和 crystal knowledge 中生成 reflect insights。

Insight MUST 包含 id、title、content、sourceIds、concepts、confidence、reinforcements、createdAt 和 updatedAt。系统 MUST 基于多个相关 knowledge records 生成 insight，并保留 provenance。重复 insight MUST 强化已有 insight。

#### Scenario: Generate insight from knowledge cluster

- **WHEN** 多条 knowledge 在 concepts 或 source relations 上形成相关 cluster
- **THEN** 系统使用 LLM 生成高层 insight 并保存 source ids

#### Scenario: Reinforce existing insight

- **WHEN** 新 insight 与已有 insight fingerprint 相同
- **THEN** 系统强化已有 insight 而不是新增重复 insight

### Requirement: Wiki Lint

系统 SHALL 支持 LLM Wiki 健康检查。

Wiki lint MUST 返回结构化问题列表，至少支持 `contradiction`、`stale`、`low_confidence`、`missing_source` 和 `orphan`。Lint MUST include severity、message、sourceIds 和 suggestedAction。Lint MUST 让 LLM 读取 knowledge、insights 和 Wiki pages 后判断 contradiction/stale 问题，并将 deterministic missing-source、low-confidence 和 orphan 检查作为补充。LLM provider 不可用时，系统 MUST 返回明确错误。第一版 lint MUST NOT 默认自动修改或删除 records。

#### Scenario: Report stale or contradictory knowledge

- **WHEN** lint 发现知识之间存在潜在矛盾或陈旧结论
- **THEN** 系统返回 lint issue 和建议操作

#### Scenario: LLM detects stale conclusion

- **WHEN** 新 evidence 推翻或削弱已有结论
- **THEN** LLM lint 返回 stale 或 contradiction issue，并保留相关 source ids

#### Scenario: Report missing provenance

- **WHEN** knowledge 或 Wiki page 缺少 source ids
- **THEN** 系统返回 missing_source issue

### Requirement: Query Filing

系统 SHALL 支持将高价值 query answer 沉淀回 LLM Wiki 知识层。

Query filing MUST 接收 query、content、kind、sourceIds、concepts 和 confidence。系统 MUST 保存为 knowledge、insight 或 crystal，并为其创建 search document。系统 MUST 保留 query 和 source ids，避免把无来源分析保存为高置信知识。

#### Scenario: File query answer as insight

- **WHEN** 用户提交 query answer 并指定 kind 为 insight
- **THEN** 系统保存 insight 并索引

#### Scenario: File query answer with provenance

- **WHEN** query filing payload 包含 source ids
- **THEN** 保存的 record 保留这些 source ids

#### Scenario: Reject empty query filing

- **WHEN** query 或 content 为空
- **THEN** 系统拒绝请求并返回结构化错误
