## Context

AgentMemory 当前已经具备核心后端能力：health/provider 状态、sessions、memories、summaries、memory candidates、audit、LLM processing jobs、search、smart-search 和 index 管理。用户目前需要通过 CLI 或 REST 手动查看这些数据，缺少一个第一版可视化入口。

Viewer 的目标是让用户验收和查看已有数据，不在本 change 中引入新的长期知识抽取机制。关系图先基于已有 record metadata 生成，避免提前实现独立 knowledge graph。

## Goals / Non-Goals

**Goals:**

- 由 `agentmemory serve` 托管 `/agentmemory/` Viewer。
- Viewer 第一屏展示服务状态、provider 状态和 index status。
- 展示 memories、sessions、summaries、memory candidates、audit 和 LLM processing jobs。
- 提供 search 和 smart-search 表单，展示 results、evidence 和 context。
- 提供轻量关系图视图，基于已有数据中的 `sessionId`、`project`、`files`、`concepts`、memory、summary 关系生成。
- 保持只读，不修改业务数据。
- 保持实现简单，优先单页静态资源和现有 REST endpoints。

**Non-Goals:**

- 不实现 Wiki 页面。
- 不实现候选记忆转正、编辑、删除、导入或导出。
- 不实现 Hook、MCP 或自动采集。
- 不实现独立图谱抽取、graphNodes/graphEdges 持久化或 LLM 图谱生成。
- 不实现复杂认证或多用户权限。
- 不引入大型前端工程，除非实现阶段确认必要。

## Decisions

### 1. 使用 FastAPI 静态托管第一版 Viewer

第一版 Viewer 可以作为静态 HTML/CSS/JS 由 FastAPI 直接托管，入口为 `/agentmemory/`。这样不需要单独前端 dev server、构建链或运行时依赖，便于本地验收。

后续如果 Viewer 复杂度上升，再迁移到 Vite + React。

### 2. Viewer 只消费现有 REST API

Viewer 应优先调用现有 endpoints：

- `/agentmemory/health`
- `/agentmemory/sessions`
- `/agentmemory/memories`
- `/agentmemory/summaries`
- `/agentmemory/memory-candidates`
- `/agentmemory/llm-processing-jobs`
- `/agentmemory/audit`
- `/agentmemory/search`
- `/agentmemory/smart-search`
- `/agentmemory/index/status`
- `/agentmemory/index/repair`

这样避免重复业务逻辑，也能顺带验证 REST API 是否适合外部集成。

### 3. 关系图前端派生

第一版关系图由 Viewer 前端从已有数据派生：

- memory -> concept
- memory -> file
- summary -> session
- observation/search result -> session
- session -> project

这满足“有一个关系图可看”的第一版诉求，同时不引入图谱存储和 LLM 抽取。

### 4. 产品界面偏运维/知识库，而不是营销页

Viewer 是日常工具，不做 landing page。第一屏直接展示状态、搜索和数据导航。视觉上保持信息密度、清晰扫描和稳定布局。

## Risks / Trade-offs

- 静态 HTML/JS 可维护性有限 -> 第一版控制交互范围；复杂后再迁移 React。
- 前端派生图谱不如持久图谱准确 -> 明确第一版仅用于查看和导航，不参与搜索排序。
- 数据量大时列表变长 -> 第一版限制显示数量和提供搜索，后续再做分页。
- smart-search 调用 LLM 有成本和延迟 -> Viewer 明确区分普通 search 和 smart-search，由用户主动触发。
