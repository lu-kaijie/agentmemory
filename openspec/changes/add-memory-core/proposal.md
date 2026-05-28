## Why

服务底座已经可运行，但系统还不能保存 agent 工作过程或用户显式记忆。需要先实现最小记忆核心，让后续 RAG、LLM Wiki 和 Viewer 有稳定的数据来源。

本变更建立 session、observation、memory 和 audit 四个核心状态域，并通过 REST 与 CLI 提供写入和查看能力。

## What Changes

- 新增核心数据模型：session、observation、memory、audit。
- 新增内部业务函数层，封装 `observe`、`remember`、list sessions、list memories、list audit。
- 新增 REST API：
  - `POST /agentmemory/observe`
  - `POST /agentmemory/remember`
  - `GET /agentmemory/sessions`
  - `GET /agentmemory/memories`
  - `GET /agentmemory/audit`
- 新增 CLI 命令：
  - `agentmemory observe`
  - `agentmemory remember`
  - `agentmemory sessions`
  - `agentmemory memories`
  - `agentmemory audit`
- 新增基础审计：保存 observation 和 memory 时写入 audit。
- 保留 `language` 字段，为中文、英文和中英混合内容的后续检索做准备。
- 不实现 RAG、FTS5、LanceDB、LLM 摘要、LLM Wiki 或搜索。

## Capabilities

### New Capabilities

- `memory-core`: session、observation、memory 和 audit 的基础保存、读取和审计能力。
- `memory-core-interfaces`: memory core 的 REST 和 CLI 接入能力。

### Modified Capabilities

无。

## Impact

- 新增内部函数模块、Pydantic schema、REST routes、CLI commands 和测试。
- 扩展 `StateKV` 使用的 scope 常量，但不改变底层 KV 表结构。
- 后续 `add-rag-search` 可以基于 observation、memory 和 audit 数据实现索引和检索。
