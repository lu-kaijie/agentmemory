## Context

当前仓库只有产品文档和 OpenSpec 规划，还没有可运行代码。`bootstrap-python-service` 是实现阶段的第一个小变更，目标是建立 Python/FastAPI 底座，让后续记忆、RAG、LLM Wiki 和 Viewer 能按模块逐步落地。

本变更聚焦基础设施，不实现业务记忆能力。完成后，开发者应能安装依赖、启动服务、调用健康检查、运行 CLI doctor，并通过 `StateKV` 写入和读取基础状态。

## Goals / Non-Goals

**Goals:**

- 建立 Python 3.11+ 包结构和 `pyproject.toml`。
- 使用 FastAPI 提供最小 REST 服务。
- 使用 Typer 提供 CLI 入口。
- 使用 Pydantic Settings 管理配置。
- 使用 SQLite + SQLAlchemy 实现 `StateKV` 基础抽象。
- 提供 `/agentmemory/health`、`/agentmemory/livez`、`agentmemory serve`、`agentmemory doctor`。
- 提供 pytest 测试，覆盖配置、健康检查、CLI 和 StateKV。

**Non-Goals:**

- 不实现 `observe`、`remember`、`search`、`smart-search`。
- 不接入 LLM provider、embedding provider 或 LanceDB。
- 不实现 Skill、Web Viewer、RAG、LLM Wiki、知识图谱。
- 不设计完整业务 KV scope，只保留基础 scope 字符串能力。

## Decisions

### 1. Python 包结构

源码使用 `src/agentmemory/` 布局：

- `agentmemory/config.py`：配置和敏感值隐藏。
- `agentmemory/api/app.py`：FastAPI app factory。
- `agentmemory/api/routes/health.py`：健康检查路由。
- `agentmemory/cli.py`：Typer CLI。
- `agentmemory/state/kv.py`：`StateKV`。
- `agentmemory/state/schema.py`：基础 KV scope 常量。

`src` 布局能减少测试误导导入本地目录的风险，适合后续打包发布。

### 2. 配置

使用 `pydantic-settings` 读取环境变量和 `.env`。第一版配置包括：

- `AGENTMEMORY_HOST`
- `AGENTMEMORY_PORT`
- `AGENTMEMORY_DB_PATH`
- `AGENTMEMORY_SECRET`
- `AGENTMEMORY_LOG_LEVEL`

`AGENTMEMORY_SECRET` 不在 health 响应和日志中明文输出。

### 3. REST 服务

FastAPI app 通过 `create_app(settings=None)` 创建，便于测试注入临时配置。健康检查分为：

- `/agentmemory/livez`：进程存活检查，只返回 alive。
- `/agentmemory/health`：返回服务名、版本、状态、数据库可用性和配置摘要。

### 4. CLI

Typer CLI 提供：

- `agentmemory serve`：启动 Uvicorn。
- `agentmemory doctor`：检查配置、数据库路径和 health app 初始化。

CLI 输出默认面向人类；后续 change 再统一补 `--json` 到所有业务命令。

### 5. StateKV

`StateKV` 使用一张通用表保存 JSON 值：

- `scope TEXT`
- `key TEXT`
- `value TEXT`
- `created_at TEXT`
- `updated_at TEXT`

主键为 `(scope, key)`。P0 只需要基础 `get`、`set`、`delete`、`list`，高级索引和事务封装后续再加。

## Risks / Trade-offs

- SQLite JSON 通用表不适合复杂查询 -> 后续业务功能通过专用索引表和 FTS5 扩展，不让基础 KV 承担搜索职责。
- CLI serve 直接启动 Uvicorn 可能和测试环境耦合 -> app factory 独立，测试使用 FastAPI TestClient。
- 配置项后续会增长 -> Pydantic Settings 统一集中管理，避免散落读取环境变量。

## Migration Plan

这是初始代码变更，没有历史数据迁移。

实施顺序：

1. 创建 Python 项目结构和依赖配置。
2. 实现配置模块。
3. 实现 StateKV 和 SQLite 初始化。
4. 实现 FastAPI app 和健康检查。
5. 实现 Typer CLI。
6. 添加 pytest 测试。
