## ADDED Requirements

### Requirement: Project Profile State
系统 SHALL 为每个 project 维护 Project Profile。

Project Profile MUST 包含 projectId、overview、goals、techStack、keyFiles、commands、conventions、commonIssues、sourceIds、confidence、createdAt 和 updatedAt。Profile MUST 面向 agent context 注入，表达项目当前最重要的背景。

#### Scenario: Create project profile
- **WHEN** 项目有足够 evidence
- **THEN** 系统使用 LLM 生成 Project Profile 并保存 source ids

#### Scenario: Read project profile
- **WHEN** 用户或 agent 请求项目画像
- **THEN** 系统返回该 project 的 Project Profile

### Requirement: Project Profile Update
系统 SHALL 支持显式和维护任务触发 profile update。

Profile update MUST 把现有 profile、project evidence、Wiki knowledge、summaries 和 important memories 交给 LLM。LLM MUST 返回固定结构字段。系统 MUST 保留 sourceIds 和 confidence。

#### Scenario: Update profile from evidence
- **WHEN** 用户运行 project profile update
- **THEN** 系统用 LLM 整合项目 evidence 并更新 profile

#### Scenario: Maintenance updates profile
- **WHEN** maintenance run 发现 project 有新 summaries 或 Wiki knowledge
- **THEN** 系统可以触发 profile update

### Requirement: Project Profile Context Section
系统 SHALL 把 Project Profile 作为 project context 的高优先级 section。

Context packing MUST 在 raw evidence 前展示 profile。Profile 内容 MUST 使用固定字段，不得混入未标源的推测。

#### Scenario: Context includes profile
- **WHEN** project profile 存在且 agent 请求该 project context
- **THEN** context 输出包含 project profile section
