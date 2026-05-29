## Context

AgentMemory 当前已经提供 CLI、REST API、LLM processing、关键词检索、向量检索和 smart-search。缺口不是新的后端能力，而是 agent 侧的使用协议：agent 需要知道什么时候查询、什么时候保存、如何避免高频调用影响当前工作流。

本变更使用 `skill-creator` 的原则设计 Skill：内容保持精简，触发描述清楚，正文只放必要流程和约束，不把 Skill 写成完整产品说明书。Skill 本体使用中文，命令、路径、字段名保持英文。

## Goals / Non-Goals

**Goals:**

- 创建 `skills/agentmemory/SKILL.md`。
- Skill 使用中文编写。
- Skill frontmatter 包含准确的 `name` 和 `description`。
- Skill 明确 CLI 优先、REST 兜底。
- Skill 明确低频调用策略，避免拖慢 agent 当前任务。
- Skill 明确查询、保存、观察记录和索引维护的触发场景。
- Skill 给出最小必要命令示例，并要求查询类命令优先使用 `--json`。
- 增加测试确保 Skill 存在、frontmatter 有效、正文不包含当前版本排除的接入方式。

**Non-Goals:**

- 不实现 Hook。
- 不实现 MCP。
- 不实现 Web Viewer、Wiki、context、export 或 delete。
- 不创建额外 README、quick reference 或安装指南。
- 不把用户密钥、模型配置或环境变量值写入 Skill。

## Decisions

### 1. Skill 放在仓库内 `skills/agentmemory/SKILL.md`

仓库内 Skill 便于版本管理、测试和后续打包。当前阶段不自动安装到全局 Codex skills 目录，避免影响用户已有环境。

### 2. Skill 正文保持中文和短流程

用户明确要求中文；agent 能理解中文命令说明。正文以操作决策为主，不重复解释 FTS5、LanceDB、LLM Wiki 等背景知识。

### 3. CLI 优先，REST 兜底

CLI 对多数 coding agent 更通用，也更容易在 shell 工具中调用。REST API 保留给 CLI 不可用、已有服务在运行或 agent 更适合发 HTTP 请求的场景。

### 4. 低频触发写入

`observe` 会触发 LLM processing，索引也会创建后台任务。Skill 必须要求 agent 只在阶段性节点调用，而不是在每次文件读取、编辑或测试后调用。

### 5. 不包含 Hook/MCP 说明

第一版范围明确不做 Hook/MCP。Skill 不能暗示当前版本支持这些接入方式，否则会让 agent 误用不存在的能力。

## Risks / Trade-offs

- Skill 过长导致 agent 不读重点 -> 控制在一个简洁 `SKILL.md` 内，不添加额外参考文件。
- Skill 过于保守导致记忆不足 -> 明确“任务开始、用户提到历史、关键决策、阶段结束”这些必须或应该调用的场景。
- CLI 和 REST 双入口造成混乱 -> 明确默认 CLI 优先，只有 CLI 不可用时使用 REST。
- 当前缺少 context/wiki/export/delete -> Skill 只描述已实现命令，避免超前承诺。
