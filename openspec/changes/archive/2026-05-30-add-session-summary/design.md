## Context

当前 session 只在 `observe` 时被动创建和更新。Skill 可以指导 agent 在会话边界调用 `context` 和 `observe`，但状态层没有显式 start/end，也不能把一次会话的 observations 汇总成会话级 summary。后续自动接入需要稳定的 session lifecycle 接口，而不是直接依赖普通 observation 的约定。

## Goals / Non-Goals

**Goals:**

- 增加显式 session start/end 的 core、CLI 和 REST 能力。
- session 记录保存生命周期字段：`status`、`endedAt`、`summaryId`。
- session end 时基于该 session 的 observations 生成会话级 summary，写入 summary、搜索索引和 Wiki 更新队列。
- Skill 先提供轻量会话生命周期约定，让当前 shell-based agent 不等自动接入也能使用。

**Non-Goals:**

- 本 change 不实现 Hook 或 MCP 自动触发。
- 不改变现有 `observe` 自动创建 session 的兼容行为。
- 不做多会话冲突锁、后台异步 session summarization 或复杂 timeline UI。

## Decisions

- **复用 `SummaryRecord` 保存 session summary。** 增加 `kind=observation|session`、`sessionId` 和可空 `observationId`，这样 search/context/wiki 可以继续把 summary 当作同一类 evidence 处理。
- **session end 同步生成 summary。** 当前 `observe` 已同步执行 LLM processing，session end 保持一致，失败时保留 session ended 状态并返回 `summary=null`。
- **start 幂等创建或更新。** `session start` 接收可选 `sessionId`；存在则刷新项目/cwd/status，不存在则创建，便于 agent 显式指定稳定 id，也兼容不指定 id。
- **end 不新增 observation。** 会话级 summary 是 session 聚合结果，不把结束动作伪装成普通 observation，避免 observationCount 失真。
- **Skill 约定先落地。** Skill 在实现 Hook 前要求 agent 在任务开始先取 context，在结束前调用 session end；如果正式命令不可用，再用 `observe --type work-summary` 作为降级。

## Risks / Trade-offs

- **已有 summary 数据没有 `kind/sessionId` 字段** → Pydantic 默认值保持旧数据可读，`summary_document` 从 observation 回填 sessionId。
- **LLM 失败导致 session 没有 summary** → end response 保留 session 状态和错误信息，后续重试能力另行处理。
- **同步 session end 可能较慢** → 第一版与现有 LLM processing 行为一致，后续后台任务再优化。
- **Skill 调用无法强制 agent 遵守** → 这是轻量约定，正式 CLI/REST 能力为后续自动触发提供稳定入口。
