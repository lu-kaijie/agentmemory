## ADDED Requirements

### Requirement: Scoped Wiki Records
系统 SHALL 支持 global 和 project scoped Wiki records。

Knowledge、insight 和 wikiPage MUST 能绑定 scope/projectId。LLM Wiki consolidation MUST 在指定 scope 下运行。Project consolidation MUST 使用 global records 作为背景，但 MUST 不把项目特定结论写入 global scope。

#### Scenario: Project wiki consolidation
- **WHEN** 用户对某 project 运行 wiki consolidate
- **THEN** 系统生成或更新 project scoped knowledge、insight 和 wiki pages

#### Scenario: Global wiki consolidation
- **WHEN** 用户对 global scope 运行 wiki consolidate
- **THEN** 系统只使用跨项目 evidence 或明确 global records 生成 global knowledge

### Requirement: Wiki Synthesis For Context
系统 SHALL 为 agent context 提供 Wiki synthesis。

Wiki synthesis MUST 是由 LLM consolidation/reflect 生成的高层内容。Context MUST 优先使用 synthesis，而不是把多个 raw wikiPage/knowledge records 直接堆叠。

#### Scenario: Context uses wiki synthesis
- **WHEN** project 有 wiki synthesis 或 high-confidence insight
- **THEN** context 的 wiki-synthesis section 使用该内容
