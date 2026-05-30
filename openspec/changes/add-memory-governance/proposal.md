## Why

AgentMemory 已经可以保存、处理和检索记忆，但用户还不能完整导出数据，也不能删除错误或过期的长期记忆。P0 需要补齐治理闭环，让长期记忆可审计、可导出、可精确删除。

## What Changes

- 新增完整数据导出能力，覆盖 sessions、observations、memories、summaries、memory candidates、LLM processing jobs、index jobs 和 audit。
- 新增按 ID 删除 memory 的治理能力。
- 删除 memory 时同步移除对应 searchable document、FTS5 记录和 LanceDB 向量记录。
- 导出和删除操作写入 audit，保留操作者来源、目标实体和操作详情。
- 新增 REST 和 CLI 入口：
  - `GET /agentmemory/export`
  - `POST /agentmemory/forget`
  - `agentmemory export`
  - `agentmemory forget --memory-id <id>`
- 本变更不实现模糊删除、批量删除、自动过期、导入、候选记忆接受/拒绝或 Viewer 删除按钮。

## Capabilities

### New Capabilities

- `memory-governance`: memory 导出、精确删除和治理审计能力。

### Modified Capabilities

- `memory-core-interfaces`: 增加 export 和 forget 的 REST/CLI 接口要求。
- `memory-indexing`: 增加 memory 删除时索引记录和向量记录失效要求。

## Impact

- Core service：新增 export 和 forget 业务函数。
- StateKV：需要支持列出完整 observation 数据和删除指定 memory/search document/index 记录。
- REST API：新增 `/agentmemory/export` 和 `/agentmemory/forget`。
- CLI：新增 `export` 和 `forget` 命令，查询类输出支持 `--json`。
- Search/index：memory 删除后不得再被 keyword、vector 或 hybrid search 返回。
- Tests：新增 service、REST、CLI 和索引删除相关测试。
