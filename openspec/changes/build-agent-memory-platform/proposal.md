## Why

AI native 开发流程中，coding agent 会持续承担探索、实现、验证和复盘工作，但多数 agent 缺少可靠的长期记忆层，容易重复探索、遗忘历史决策、丢失工具执行上下文，也难以追踪哪些记忆被保存、删除或导出。

本变更将从 0 到 1 建设一个 AI native 的个人 agent memory platform。产品从第一版就以 agent-first、LLM-first、skill-guided 和 tool-callable 为原则，先形成 Skill + CLI + REST API + Web Viewer 的 P0 闭环，再为自动采集适配器、关系图谱增强、多 agent 协作和高级检索能力预留演进路径。

## What Changes

- 新建一个 AI native agent memory platform，提供 observation 采集、LLM 摘要与记忆提炼、显式 memory 保存、搜索、导出、审计和健康检查能力。
- 建立统一的状态访问层，所有 REST、CLI、Skill 间接调用和后台任务都通过内部 `mem::*` 函数读写状态。
- 提供 REST API，路径统一使用 `/agentmemory/*`。
- 提供 CLI，作为所有 shell-capable agent 的通用调用入口。
- 提供项目 Skill，指导不同 agent 何时保存、搜索、更新 Wiki 和注入上下文。
- 提供 Web Viewer，支持记忆查看、搜索、Wiki 页面、健康状态和简单关系图。
- 建立正式产品开发文档、技术设计、需求规格和任务拆解，支持后续按阶段实现。
- 不引入破坏性变更；当前仓库尚未存在生产代码，本变更为初始建设。

## Capabilities

### New Capabilities

- `memory-capture`: 采集 agent 会话、工具执行和用户显式保存的记忆，并维护 session、observation、memory 和 audit 状态。
- `memory-search`: 提供关键词搜索、embedding 搜索、智能搜索和可注入上下文输出，后续可扩展到 graph weight 和 hybrid search。
- `memory-wiki`: 提供 LLM 维护的个人知识库页面，将碎片化 observation 和 memory 沉淀为可读、可引用、可更新的 Wiki。
- `memory-interfaces`: 提供 Skill、CLI、REST 和 Viewer 等边界入口，并保证它们复用同一组内部能力。
- `memory-governance`: 提供导出、导入、删除、审计、健康检查和配置开关等治理能力。

### Modified Capabilities

无。

## Impact

- 新增 AI native 产品文档和 OpenSpec 变更文档。
- 后续实现将新增 Python/FastAPI 服务、状态层、CLI、REST API、Skill、Web Viewer、测试和本地运行脚本。
- 需要选择持久化方案、HTTP 框架、CLI 框架、测试框架、首版 LLM provider 和 embedding provider。
- 需要定义认证方式、配置项、状态 schema、错误响应格式和验收测试。
