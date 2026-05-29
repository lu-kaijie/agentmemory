## Why

AgentMemory 已经具备 CLI、REST、LLM processing 和搜索能力，但 agent 还没有统一的使用协议。下一步需要提供一个中文 Skill，让用户在全局 agent 配置中只用一句话启用 AgentMemory skill，具体行为规则全部由 Skill 承载。

## What Changes

- 新增 AgentMemory Skill 文件，作为第一版 agent 接入协议。
- Skill 本体使用中文，且不要求全局 agent 配置写具体文件路径。
- 提供推荐的一行全局配置文案：`编码任务中使用 AgentMemory skill 管理长期记忆。`
- Skill 默认指导 agent 优先调用 CLI，并在 CLI 不可用时使用 REST API。
- 明确必须查询、应该保存、应该 observe 的场景。
- 明确低频触发策略：不在每次文件读取、每次编辑、每次命令执行后调用 AgentMemory。
- 明确搜索入口：关键词/语义/混合搜索和 smart-search 的使用边界。
- 明确写入入口：`observe` 用于阶段性工作过程，`remember` 用于用户明确要求长期保留的记忆。
- 增加文档测试，确保 Skill 不包含当前版本不支持的集成方式，也不出现不应出现在正式项目文档中的来源描述。
- 不实现 Hook、MCP、Viewer、Wiki、context、export 或 delete。

## Capabilities

### New Capabilities

- `agent-skill`: AgentMemory Skill 的启用方式、使用规则、CLI/REST 调用策略、低频触发策略和安全写入约束。

### Modified Capabilities

- `memory-core-interfaces`: CLI/REST 作为 Skill 调用入口的约束和 JSON 输出要求。

## Impact

- 新增 `skills/agentmemory/SKILL.md`。
- 可能新增 Skill 文档测试。
- 不新增运行时依赖。
- 不修改已有 REST API 或 CLI 命令行为。
