## Why

当前 LLM Wiki 已能把 evidence 提炼成 knowledge 并聚合到 Wiki 页面，但还偏一次性更新，缺少“知识复利”的维护机制。需要让系统在不引入 markdown/vault 形态的前提下，吸收 LLM Wiki 思想：持续 consolidation、强化/衰减 lessons、生成 crystals 和 insights、检查陈旧/矛盾知识，并允许高价值 query 结果沉淀回知识层。

## What Changes

- 增加 Wiki consolidation 能力：从 session summaries、memories 和已有 knowledge 中提炼更稳定的 semantic/procedural knowledge。
- 增强 lesson 生命周期：支持 recall、strengthen、decay、soft delete 和来源追踪。
- 增强 crystal 生成：从近期 evidence 或 source group 生成阶段性 crystal，并可反向强化 lesson。
- 增加 reflect insights：从 semantic/procedural/lesson/crystal 中归纳更高层 insight。
- 增加 Wiki lint：检查 contradiction、stale、low-confidence、missing sourceIds 等健康问题，第一版只输出建议。
- 增加 query filing：将高价值 smart-search/context 分析结果沉淀为 knowledge/insight/crystal，而不是只留在一次对话输出里。
- 保留现有固定 Wiki topic 作为 P0 导航/聚合入口，不把固定 topic 视为完整 LLM Wiki 模型。
- 不增加 markdown/wiki vault 导出层，不改变 SQLite 结构化主存储的定位。

## Capabilities

### New Capabilities

### Modified Capabilities

- `memory-wiki`: 增加 LLM Wiki consolidation、lesson lifecycle、crystal lifecycle、reflect insights、wiki lint 和 query filing 要求。
- `memory-core-interfaces`: 增加对应 CLI/REST 接口要求。
- `memory-search`: 增加 insight/增强 knowledge 可检索并可用于 context 的要求。

## Impact

- 影响 core models、core service、Wiki processing、search document 映射、CLI、REST、maintenance、docs 和 tests。
- 新增或扩展状态记录：knowledge lifecycle 字段、insight records、lint result/report 结构。
- 不引入新外部依赖，不引入 markdown/vault 存储，不破坏现有 Wiki topic 和 search/context 兼容性。
