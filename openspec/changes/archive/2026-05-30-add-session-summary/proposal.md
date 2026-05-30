## Why

AgentMemory 现在会在 observation 写入时顺带维护 session，但缺少显式的会话开始、会话结束和会话级 summary。需要先用 Skill 约定让 agent 立即按会话边界使用 context/observe，再把 session lifecycle 产品化为 CLI、REST 和状态能力，为后续自动接入打底。

## What Changes

- 增强 AgentMemory Skill：明确新任务开始时先取 context，阶段性记录 observe，任务结束前写入会话总结。
- 增加显式 session start/end 能力：允许调用方创建或恢复 session、结束 session，并记录 `status`、`endedAt` 和 `summaryId`。
- session end 时基于本 session observations 生成会话级 summary，并让该 summary 可被 search、context 和 Wiki 使用。
- 增加 CLI 和 REST 接口：`agentmemory session start/end`、`POST /agentmemory/session/start`、`POST /agentmemory/session/end`。
- 保持现有 observe 自动创建 session 的行为，兼容没有显式 start 的调用方。

## Capabilities

### New Capabilities

### Modified Capabilities

- `agent-skill`: 增加基于 Skill 的轻量会话生命周期使用约定。
- `memory-core`: 增加显式 session start/end、session summary 字段和会话级 summary 生成要求。
- `memory-core-interfaces`: 增加 session start/end CLI 与 REST 接口要求。
- `memory-indexing`: 明确 session summary 作为 summary document 进入索引。
- `memory-wiki`: 明确 session summary 可触发 Wiki 更新。

## Impact

- 影响 `skills/agentmemory/SKILL.md`。
- 影响 core models、service、search/indexing、CLI、REST API、Viewer 展示和测试。
- 需要更新 OpenSpec 当前 specs 和 `build-agent-memory-platform` 任务进度。
- 不引入新外部依赖，不改变现有 observe/remember/search/context 调用兼容性。
