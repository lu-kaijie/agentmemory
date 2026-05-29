## Why

AgentMemory 已经能保存、处理和检索长期记忆，但用户目前只能通过 CLI/REST 查看数据。下一步需要提供第一版 Web Viewer，让用户能直观看到服务状态、记忆内容、搜索结果和简单关系图，便于验收和日常使用。

## What Changes

- 新增 Web Viewer 第一版，由 `agentmemory serve` 托管。
- 提供 `/agentmemory/` 页面作为 Viewer 入口。
- 展示 health、provider 和 index status。
- 展示 sessions、memories、summaries、memory candidates、audit 和 LLM processing jobs。
- 提供搜索界面，支持 keyword/vector/hybrid search 和 smart-search。
- 提供简单关系图视图，基于已有 records 的 session、memory、summary、concept、file、project 关系生成，不引入独立知识图谱抽取。
- 保持 Viewer 只读，不实现编辑、删除、导入、导出或候选记忆转正。
- 不实现 Wiki 页面维护、Hook、MCP、认证体系或复杂前端工程。

## Capabilities

### New Capabilities

- `web-viewer`: Viewer 的静态资源托管、页面结构、数据展示、搜索交互和简单关系图。

### Modified Capabilities

- `memory-core-interfaces`: 增加 Viewer 静态入口和只读数据访问约束。

## Impact

- 新增 Viewer 静态文件或轻量前端模块。
- 修改 FastAPI app 以托管 `/agentmemory/` Viewer。
- 可能新增只读图谱数据 endpoint，或在 Viewer 前端基于现有 endpoints 组装图谱。
- 增加 Viewer 相关 API/HTML 测试。
- 不新增后端数据模型作为第一版必需项。
