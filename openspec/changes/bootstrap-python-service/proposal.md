## Why

AgentMemory 需要先建立一个可运行、可测试、可扩展的 Python/FastAPI 底座，后续记忆采集、RAG、LLM Wiki、Viewer 和治理能力才能在稳定边界上逐步实现。

本变更只搭建第一层基础设施，目标是让仓库具备标准 Python 项目结构、配置系统、REST 健康检查、CLI 启动入口和 SQLite StateKV 基础能力。

## What Changes

- 初始化 Python 3.11+ 项目结构和 `pyproject.toml`。
- 引入 FastAPI、Uvicorn、Typer、Pydantic v2、pydantic-settings、SQLAlchemy、pytest 等基础依赖。
- 新增配置模块，统一读取环境变量和 `.env`，并隐藏敏感配置。
- 新增 FastAPI app，提供 `/agentmemory/health` 和 `/agentmemory/livez`。
- 新增 Typer CLI，提供 `agentmemory serve` 和 `agentmemory doctor`。
- 新增 SQLite 连接和 `StateKV` 抽象，支持基础 `get`、`set`、`delete`、`list`。
- 新增最小测试，验证配置、健康检查、CLI 和 StateKV。
- 不实现 observation、memory、RAG、LLM Wiki、LanceDB、Viewer 或知识图谱。

## Capabilities

### New Capabilities

- `python-service-foundation`: Python/FastAPI 服务底座、配置、CLI、健康检查和本地运行能力。
- `state-kv-foundation`: SQLite-backed `StateKV` 基础状态层，供后续内部函数复用。

### Modified Capabilities

无。

## Impact

- 新增 Python 包源码目录、测试目录、项目配置和 CLI 入口。
- 新增本地 SQLite 数据文件配置项，但不引入业务 schema。
- 后续 change 可以在该底座上实现 memory capture、RAG search、LLM Wiki 和 Viewer。
