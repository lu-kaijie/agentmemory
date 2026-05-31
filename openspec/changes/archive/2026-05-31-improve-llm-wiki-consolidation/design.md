## Context

当前项目已经具备 observation、memory、summary、knowledge、Wiki page、search/context 和 maintenance。它已经能把单次 evidence 经 LLM 提炼为 knowledge，并聚合进固定 Wiki topic 页面。但 LLM Wiki 思想的重点不是固定页面，而是持续维护一个会积累、会修订、会强化、会反思的长期知识层。

本设计参考结构化长期记忆系统的做法，但不引入 markdown/vault 作为主目标。当前项目继续以 SQLite 结构化状态为主存储，以 CLI/REST/search/context 作为主要交互面。

## Goals / Non-Goals

**Goals:**

- 增加 `wiki consolidate`，把多条 summaries、memories 和 knowledge 中反复出现的内容沉淀为更稳定的 semantic/procedural knowledge。
- 增强 lesson 生命周期：recall、strengthen、decay、soft delete、sourceIds 和 audit。
- 增强 crystal：按 source group 生成阶段性 digest，并反向强化 lessons。
- 增加 reflect insights：从 semantic/procedural/lesson/crystal 中合成更高层 insight，并进入 search/context。
- 增加 wiki lint：输出 contradiction、stale、low-confidence、missing sourceIds 等健康报告。
- 增加 query filing：把高价值 query answer 沉淀回 knowledge/insight/crystal。
- 保留 6 个固定 Wiki topic 作为导航入口和兼容层，同时支持 LLM 生成动态 entity/concept/source/comparison/synthesis 页面。

**Non-Goals:**

- 不实现 markdown/wiki vault 导出。
- 不引入 Obsidian、Dataview、Marp 或 markdown 专用依赖。
- 不把 Wiki 主存储迁移出 SQLite。
- 不实现完整知识图谱持久化。
- 不让 lint 默认自动改写或删除知识；第一版只报告建议。

## Decisions

### 1. 结构化状态优先

继续使用 `KnowledgeRecord` 和新增 `InsightRecord` 等结构化记录作为主知识层，而不是把 markdown 文件作为主状态。

原因：

- CLI、REST、search、context 已围绕 Pydantic records 和 `StateKV` 建立。
- 结构化字段更适合重试、审计、过滤、测试和导入导出。
- 后续仍可增加 markdown 导出，但不会阻塞核心能力。

### 2. 固定 Wiki topic 保留为导航入口，动态页面承载增长

现有 6 个 topic 继续保留，用于 P0 Viewer 和 context 的可读入口。新 consolidation 不以“写入 6 页”为终点，而是优先强化 knowledge 层，并允许 LLM 创建 entity、concept、source、comparison、synthesis 等动态页面。动态页面仍带有 parent topic，便于导航和兼容旧入口。

原因：

- 保持兼容。
- 让固定 topic 负责导航，动态页面负责持续增长的实体、概念、来源和对比。
- 让 Wiki page 成为 knowledge 的聚合视图，而不是完整知识模型。

### 3. Consolidation 和 Wiki update 分离

`wiki update` 处理新增 evidence；`wiki consolidate` 周期性处理跨 evidence 的稳定化。

原因：

- 单条 evidence 更适合生成 summary、candidate 和初步 knowledge。
- 稳定事实/流程应该由多条 evidence 支撑，避免过早固化。
- maintenance 可以定期调用 consolidation，但 CLI/REST 也可手动触发。

### 4. Lesson 和 crystal 使用 lifecycle 字段

Lesson 使用 `reinforcements`、`lastReinforcedAt`、`decayRate`、`lastDecayedAt`、`deleted`。Crystal 使用 `sourceGroup`、`sourceIds`、`files`、`concepts` 和 confidence。

原因：

- Lesson 需要能被重复强化，也需要长期不用时降低置信。
- Crystal 需要稳定边界，避免相同 source group 重复生成。

### 5. Reflect insight 独立于 Wiki page

Insight 是跨 facts、procedures、lessons、crystals 的高层归纳，作为独立 sourceType 或 knowledge kind 进入检索。

原因：

- Insight 不一定属于某个固定 Wiki topic。
- Reflect 是 LLM Wiki 的 synthesis 层，不应被页面结构限制。

### 6. LLM 优先判断 consolidation 和 lint

`wiki consolidate` 和 `wiki lint` 都要求 LLM provider。Consolidation、contradiction 和 stale 判断属于语义维护任务，LLM 不可用时返回明确错误； deterministic checks 只补充 `missing_source`、`low_confidence`、`orphan` 这类结构字段问题。

原因：

- 稳定事实、冲突、陈旧结论和可合并页面需要跨 evidence 的语义判断。
- 单纯关键词或 fingerprint 无法可靠判断“新证据是否推翻旧结论”。
- 结构化 XML 输出让结果仍能被测试、审计和索引。
- 失败显式暴露，避免无 LLM 时用关键词规则生成看似有效但语义质量不足的 Wiki 结果。

### 7. Lint 先报告，不自动修复

第一版 `wiki lint` 返回问题列表和建议，不自动编辑 knowledge 或 Wiki pages。

原因：

- contradiction/stale 判断可能误伤。
- 用户/agent 可以先检查 lint 报告，再决定是否 file answer、remember 或重新 consolidate。

## Risks / Trade-offs

- [Risk] Consolidation 可能生成重复或过早稳定的知识。  
  Mitigation: 使用最小证据数、fingerprint、sourceIds 和 confidence；不确定时保留为低 confidence 或跳过。

- [Risk] Lesson decay 可能降低仍有价值但近期未使用的经验。  
  Mitigation: soft delete 而非物理删除；recall/strengthen 可恢复置信。

- [Risk] Reflect insight 可能抽象过度。  
  Mitigation: 保留 sourceIds、confidence 和 evidence，context 中仍可追溯。

- [Risk] 新命令增加使用复杂度。  
  Mitigation: maintenance 可统一调度；README/Skill 只暴露常用入口。

## Migration Plan

- 旧 knowledge records 缺少新增 lifecycle 字段时使用 Pydantic 默认值。
- 现有 Wiki pages、jobs、search documents 保持兼容。
- 新增 insight/knowledge 字段后，`index repair` 可补齐 search documents。
- 回滚时保留新增 records 不影响旧命令读取。

## Open Questions

- Insight 是否作为新 `SourceType`，还是作为 `knowledge.kind="insight"`？第一版建议新增 `InsightRecord` 和 `sourceType="insight"`，便于独立生命周期和检索过滤。
- Query filing 的输入是 `query + answer`，还是直接引用最近一次 smart-search 结果？第一版建议显式传入 query/content/sourceIds，避免隐式状态。
