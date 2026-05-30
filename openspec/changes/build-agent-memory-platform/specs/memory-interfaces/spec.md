## ADDED Requirements

### Requirement: Skill Instructions

系统 SHALL 提供项目 Skill，用于指导不同 agent 何时保存记忆、何时搜索、何时读取上下文、何时更新 Wiki。

Skill MUST 以 CLI 为首选调用方式，并提供 REST API 兜底方式。
Skill MUST 明确 search、smart-search、context、remember、observe 和 wiki 命令的触发场景，并要求查询类命令优先使用 `--json` 输出。

#### Scenario: Agent follows skill to search memory

- **WHEN** agent 开始一个需要历史上下文的任务
- **THEN** Skill 指导 agent 调用 `agentmemory search`、`agentmemory smart-search`、`agentmemory context` 或对应 REST 接口

#### Scenario: Agent follows skill to save stable memory

- **WHEN** 用户明确要求记住偏好、决策或项目约定
- **THEN** Skill 指导 agent 调用 `agentmemory remember --json`

#### Scenario: Agent follows skill to record work observation

- **WHEN** agent 完成一次有价值的探索、修改、验证或阶段总结
- **THEN** Skill 指导 agent 调用 `agentmemory observe --json`

#### Scenario: Agent handles low confidence context

- **WHEN** `agentmemory context --json` 返回低 confidence 或 evidence 不足
- **THEN** Skill 指导 agent 继续搜索、查看 evidence，或向用户说明不确定

### Requirement: CLI

系统 SHALL 提供 CLI，作为所有 shell-capable agent 的通用接入方式。

P0 MUST 提供 `serve`、`observe`、`remember`、`search`、`smart-search`、`context`、`wiki`、`index`、`export`、`forget` 和 `doctor` 命令。

#### Scenario: CLI remember saves memory

- **WHEN** agent 调用 `agentmemory remember`
- **THEN** CLI 调用 REST API 或内部函数保存 memory

#### Scenario: CLI context returns agent-friendly JSON

- **WHEN** agent 调用 `agentmemory context --json`
- **THEN** CLI 返回包含 context、evidence、wikiPages、knowledge、memories、confidence 和 compressed 的结构化 JSON

### Requirement: REST API

系统 SHALL 提供 `/agentmemory/*` REST API，并通过 adapter 调用内部 `mem::*` 能力。

P0 MUST 提供 `/agentmemory/observe`、`/agentmemory/search`、`/agentmemory/smart-search`、`/agentmemory/context`、`/agentmemory/remember`、`/agentmemory/export`、`/agentmemory/forget`、`/agentmemory/wiki/pages`、`/agentmemory/wiki/jobs`、`/agentmemory/wiki/knowledge`、`/agentmemory/wiki/update`、`/agentmemory/wiki/rebuild` 和 `/agentmemory/health`。

#### Scenario: REST observe succeeds

- **WHEN** 客户端向 `/agentmemory/observe` 提交合法 payload
- **THEN** REST adapter 校验字段并调用 `mem::observe`

#### Scenario: REST context succeeds

- **WHEN** 客户端向 `/agentmemory/context` 提交合法 payload
- **THEN** REST adapter 校验字段并返回 context response

### Requirement: Viewer

系统 SHALL 提供 Web Viewer，用于查看 sessions、memories、Wiki 页面、health 和基础关系图。

#### Scenario: Viewer shows health

- **WHEN** 用户打开 Viewer
- **THEN** 页面展示服务版本、健康状态、记忆列表、Wiki 页面和关系图入口
