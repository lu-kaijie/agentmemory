## Context

Viewer 第一版是单 HTML/CSS/JS，由 FastAPI 直接返回。这个实现满足了早期只读验收，但不适合继续承载 Global / Project scope、project profile、pinned memory、context sections、动态 Wiki 页面和关系图交互。

项目技术路线已确定 Viewer 使用 Vite + React + React Flow。当前 change 将 Viewer 从临时静态文件迁移为正式前端工程，同时继续保持本地服务简单：开发时用 Vite，发布时由 FastAPI 托管 build 产物。

## Decisions

### 1. 使用 Vite + React

React 适合当前 Viewer 的状态管理、列表筛选、详情面板和图谱交互。Vite 提供轻量构建，产物可以直接复制到 Python package。

### 2. 使用 CSS Modules

第一版不引入设计系统或 Tailwind。CSS Modules 足够隔离样式，并保持构建复杂度低。

### 3. 使用 React Flow

关系图需要拖拽、缩放、节点类型、边、点击详情和后续邻居展开。React Flow 比手写 SVG/canvas 更适合维护。

### 4. FastAPI 托管构建产物

`agentmemory serve` 仍是统一入口。Viewer route 先尝试读取 packaged build 的 `index.html`，静态资源通过 `/agentmemory/assets/*` 返回。

### 5. Viewer 只读

Viewer 主要用于观察 agent 自动写入的长期记忆。写入、删除和维护仍由 CLI/REST 明确触发，避免误操作。

## Risks

- Node build 进入 Python repo 会增加依赖面。Mitigation: 前端依赖只在开发/构建时需要，运行时只需要静态产物。
- 打包路径可能影响 wheel include。Mitigation: 显式配置 package force-include，并加测试检查 Viewer route。
- React Flow bundle 较大。Mitigation: Viewer 是本地工具，P0 接受该体积换取交互能力。
