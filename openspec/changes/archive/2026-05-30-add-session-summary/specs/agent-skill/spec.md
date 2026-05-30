## ADDED Requirements

### Requirement: Skill Session Lifecycle Guidance

Skill SHALL 指导 agent 使用轻量会话生命周期约定。

Skill MUST 要求 agent 在新任务开始时调用 `agentmemory context "<task>"` 获取外部长期记忆上下文。Skill MUST 要求 agent 在阶段性完成时使用低频 `observe` 记录关键进展。Skill MUST 要求 agent 在任务结束前优先调用 `agentmemory session end` 生成会话级 summary；当 session end 命令不可用时，Skill MUST 指导 agent 使用 `agentmemory observe --type work-summary` 写入结束总结作为降级方案。

#### Scenario: Agent starts with context

- **WHEN** agent 开始一个需要历史背景的新任务
- **THEN** Skill 指导 agent 先调用 `agentmemory context "<task>"`

#### Scenario: Agent ends with session summary

- **WHEN** agent 完成当前任务并准备结束会话
- **THEN** Skill 指导 agent 调用 `agentmemory session end` 或降级写入 `observe --type work-summary`
