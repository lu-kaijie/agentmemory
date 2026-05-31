## Why

当前 Viewer 仍是单个静态 HTML 文件，适合早期验收，但已经跟项目文档中的正式技术路线产生差距。项目文档明确 Viewer 应采用 Vite + React + React Flow，并且当前记忆模型已经升级为 Global / Project、pinned memory、project profile、fixed context sections 和动态 LLM Wiki 页面，旧 Viewer 无法清晰观察这些核心能力。

## What Changes

- 将 Viewer 前端迁移为 Vite + React。
- 使用 React Flow 实现可交互关系图。
- 保持 `/agentmemory/` 由 FastAPI 托管 Viewer。
- 增加 Global / Project 观察入口：
  - project selector
  - scope filter
  - projects/profile
  - pinned memory
  - context sections
  - scoped memories、knowledge、wiki pages、sessions
- Viewer 继续保持只读，不提供编辑、删除、导入、导出、Wiki mutation、Hook、MCP 或权限入口。
- 更新构建脚本、Python package include、测试和文档。

## Impact

- 新增前端工程目录和 Node 依赖。
- FastAPI Viewer route 改为托管构建产物。
- 测试需要覆盖构建产物、Viewer route、关键 UI 文案和 Global / Project 元素。
