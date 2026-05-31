## Context

当前项目已经有 observation、memory、summary、knowledge、insight、wikiPage、search、smart-search、context、session lifecycle 和 LLM Wiki consolidation。问题不在缺少单点能力，而在 agent 获取记忆时缺少统一层级：

- `project` 仍主要是字段过滤，不是一等实体。
- session 虽有 start/end，但不应成为用户必须管理的主模型；直接关闭 agent 时不会可靠触发 session end。
- context 主要来自 search result packing，缺少 Global / Project 的固定结构。
- 高优先级记忆和项目画像还没有正式模型。

用户目标是让 AgentMemory 从一开始就围绕全局记忆和项目记忆组织。Session 保留为内部 evidence 容器，不要求用户显式开始或结束。

## Goals / Non-Goals

**Goals:**

- 引入 `scope=global|project`，让长期记忆明确属于全局或项目。
- 引入 `ProjectRecord`，把 project 从字符串提升为一等实体。
- 让 observations/summaries/session evidence 明确归属 project，但不把 session start/end 作为正确使用的前提。
- 增加 pinned memory/slots，支持全局和项目级固定注入。
- 增加 project profile，由 LLM 从 project evidence 中整合项目目标、技术栈、关键文件、命令、约定和常见问题。
- 重构 context 输出为固定结构：
  - global
  - project
  - wiki synthesis
  - lessons and crystals
  - recent sessions
  - evidence
- 明确哪些输出需要 LLM 整合：
  - agent context、project profile、wiki synthesis、consolidation、reflect 需要 LLM synthesis 或来自已 synthesis 的长期知识。
  - list/search/audit/debug 输出保持结构化原始结果，不强制 LLM 重写。

**Non-Goals:**

- 不实现 MCP server 或 hook 自动注入；本 change 先把数据层和 context 形态打正。
- 不实现文件上下文/file history；后续可基于 project/evidence scope 增加。
- 不迁移到 markdown/vault 主存储。
- 不删除现有 search/smart-search/wiki 命令；只调整默认 context 和 scope 语义。
- 不要求所有查询输出都由 LLM 改写；否则会增加成本、延迟，并降低调试可追溯性。

## Decisions

### 1. Scope 是核心字段，不是标签

新增 `scope` 字段，取值 `global|project`。Project scoped records 必须带 `projectId` 或规范化 project key；global records 不绑定项目。

原因：

- 用户偏好、agent 使用习惯、通用 lesson 应跨项目生效。
- 项目架构、文件、命令、踩坑应只在项目内生效。
- Context 可以先注入 global，再注入 project，避免把某项目细节污染到其他项目。

备选方案是继续用 `project` 字段过滤。这个方案不够明确，无法表达 global records，也不利于 pinned/profile 的优先级排序。

### 2. Project 是一等实体

新增 `ProjectRecord`，包含 `id`、`name`、`root`、`createdAt`、`updatedAt` 和可选 metadata。CLI/REST 可以显式创建/列出项目；context/observe/remember 也可以按当前 `cwd` 自动 upsert。

原因：

- `project` 不能长期只是自由字符串。
- 后续 file context、timeline、profile、hooks 都需要稳定 project identity。
- 导入导出时可以保留项目边界。

### 3. Context 输出采用固定 envelope

### 3. 用户主模型是 Global + Project，Session 是内部 evidence 容器

本 change 不依赖 hook，也不要求用户显式 start/end session。Project 识别第一版按用户常见工作流设计：agent 在项目根目录启动，系统默认使用当前 `cwd`。展示名使用 `basename(realpath(cwd))`，内部 project id 使用 `realpath(cwd)` 的稳定 hash，避免同名目录冲突。

本 change 不引入项目内状态文件。`.agentmemory/current-session.json` 不做，因为 agent 会话可能被直接关闭，结束时未必有机会更新文件。`.agentmemory/project.json` 也不做；第一版只用 `realpath(cwd)` 识别项目。系统可以内部维护 project current active session，用于把 observations 归组和生成 summaries，但 context、remember、observe 的用户心智模型仍是 Global + Project。

原因：

- 无 hook 环境也能稳定工作。
- 关闭 agent 时不依赖清理动作。
- project 归类符合“在项目根目录启动 agent”的使用习惯。
- session 连续性由服务端 active session + TTL 尽力维护；即使没有 session end，project-level memory 仍然可用。

### 4. Context 输出采用固定 envelope

默认 prompt 输出使用固定 XML-like envelope：

```xml
<agentmemory-context source="AgentMemory" scope="project" project="...">
  <identity>...</identity>
  <global>...</global>
  <project>...</project>
  <wiki-synthesis>...</wiki-synthesis>
  <lessons-and-crystals>...</lessons-and-crystals>
  <recent-evidence>...</recent-evidence>
  <evidence>...</evidence>
</agentmemory-context>
```

每个 section 即使为空也应稳定出现或以明确空状态表示。这样 agent 不需要猜字段语义。

### 5. Agent context 是 LLM synthesis 优先，不是所有输出都 LLM

Agent-facing context 应由 LLM 整合或来自已由 LLM 整合的 records：

- project profile：LLM 从项目 evidence 维护。
- wiki synthesis：LLM consolidation/reflect 产物。
- lessons/crystals/insights：LLM 或用户显式沉淀。
- evidence：保留 source ids 和检索结果，便于核查。

普通接口保持原始结构化输出：

- `search` 返回 evidence results。
- `wiki pages/knowledge/insights` 返回 records。
- `sessions/summaries/audit/jobs` 返回状态和历史。

原因：

- Agent context 需要高信号、稳定格式、低噪声。
- Debug/list/search 需要可追溯，不应被 LLM 重新叙述后丢失字段。
- 成本和延迟可控。

### 6. Pinned memory 是 context 优先级，不是普通 memory type

Pinned memory/slots 可以引用 existing records，也可以保存独立 pinned content。它们具有 scope、priority、sourceIds、confidence 和 enabled 状态。

原因：

- 高优先级规则需要稳定注入。
- 用户纠正过的偏好、工具规则、项目约束不能被普通搜索排序挤掉。
- Pinning 是上下文策略，不只是 memory 分类。

### 7. Project profile 由 maintenance 和显式命令维护

新增 profile update 操作，输入 project evidence 和现有 profile，输出固定结构 profile。Maintenance 可以周期性更新，用户也可以手动触发。

Profile 不替代 Wiki knowledge；它是面向 agent 启动和任务上下文的 compact index。

## Risks / Trade-offs

- [Risk] 迁移现有 records 到 scope/project 可能误分类。  
  Mitigation: 默认无 project 的旧 records 进入 global 或 unknown project，并在 audit/import report 中标记。

- [Risk] Context section 太多导致 token 增加。  
  Mitigation: 每个 section 有 token budget 和优先级；evidence 可被截断但 structured evidence 列表保留。

- [Risk] LLM synthesis 可能覆盖错误结论。  
  Mitigation: 所有 synthesis 保留 sourceIds、confidence 和 updatedAt；context 中 evidence section 保留可核查来源。

- [Risk] 同一个项目从不同路径、symlink 或 worktree 打开时会生成不同 project id。  
  Mitigation: 第一版接受该限制，后续如有需要再引入 alias 或显式 project merge。

## Migration Plan

1. 新增模型和 KV scopes，保持旧字段可读。
2. 导入/读取旧 records 时补默认 scope/project。
3. 新写入路径开始写 `scope` 和 project identity。
4. Context 先兼容旧 JSON 字段，同时新增 sections。
5. 文档和 Skill 改为指导 agent 使用分层 context。

Rollback：保留旧 search/context 字段，禁用新 section packing 时仍可返回旧 context 文本。

## Open Questions

- Pinned memory 是否需要单独命令，还是复用 `remember --pinned`？建议提供独立 `pin/unpin`，避免混淆写入和注入策略。
