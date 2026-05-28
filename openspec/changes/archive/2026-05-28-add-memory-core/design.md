## Context

`bootstrap-python-service` 已提供 FastAPI、Typer、配置和 SQLite `StateKV`。当前系统可以启动和健康检查，但还不能保存任何 agent 工作记录或长期记忆。

`add-memory-core` 是第一个业务能力变更，负责建立后续 RAG 和 LLM Wiki 的数据源。实现必须保持简单：只保存、读取和审计，不做搜索索引、LLM 摘要或 Wiki 更新。

## Goals / Non-Goals

**Goals:**

- 定义 session、observation、memory、audit 的 Pydantic 模型。
- 扩展 `KV` scope 常量。
- 实现内部业务服务，封装 `observe`、`remember` 和 list 查询。
- 实现 REST API 和 CLI 命令。
- 为保存 observation、保存 memory 写入 audit。
- 保留 `language` 字段，为后续中英文混合检索准备。

**Non-Goals:**

- 不实现 FTS5、LanceDB、RAG search。
- 不实现 LLM 摘要、候选记忆提炼或 Wiki 更新。
- 不实现删除、导出、治理审计高级查询。
- 不实现认证中间件；认证可在后续统一加到 REST adapter。

## Decisions

### 1. 使用 StateKV 保存业务状态

本变更继续使用 `StateKV`，新增 scope：

- `sessions`
- `observations:<session_id>`
- `memories`
- `audit`

这样无需修改 SQLite 表结构，后续如果需要专用表或索引，可以在 RAG/Wiki change 中扩展。

### 2. ID 和时间戳

使用简单本地 ID 生成：

- session id：请求提供则使用；未提供时生成 `ses_...`。
- observation id：`obs_...`。
- memory id：`mem_...`。
- audit id：`aud_...`。

每个写入操作在开始时捕获一次 `now`，同一操作内复用该时间戳，便于审计一致性。

### 3. Observation 写入行为

`observe` 接收工作过程内容，保存 observation，并维护 session：

- 如果 session 不存在则创建。
- 每次 observation 写入更新 session 的 `observationCount` 和 `updatedAt`。
- observation 保存到 `KV.observations(sessionId)`。

### 4. Memory 写入行为

`remember` 保存用户明确要求保留的长期记忆，支持：

- `type`
- `content`
- `concepts`
- `files`
- `language`
- `canonicalId`
- `duplicateOf`
- `relations`

memory 保存到 `KV.memories`。本变更不做去重、版本化、跨语言合并或 supersede，只预留字段。跨语言近似重复需要 embedding 和 LLM 判定，放到后续 RAG/governance 阶段实现。

### 5. Audit

保存 observation 和 memory 时写 audit。audit 至少包含：

- `id`
- `action`
- `targetType`
- `targetId`
- `source`
- `timestamp`
- `details`

### 6. REST 和 CLI

REST 直接调用内部业务服务，不直接操作 `StateKV`。

CLI 默认调用本地服务地址；如果服务不可用，本变更可以直接使用本地业务服务作为 fallback，避免第一版 CLI 难以验收。CLI 查询命令支持 `--json`。

## Risks / Trade-offs

- 使用 StateKV 存列表查询简单但缺少分页效率 -> 本变更数据量小，后续搜索和 Viewer change 再增加分页和索引。
- 暂不做认证 -> 当前仍是本地开发阶段，后续 REST adapter 统一处理 bearer token。
- 暂不做去重 -> 避免过早复杂化，后续 memory governance 中加入去重和版本演进。

## Migration Plan

无历史数据迁移。

实施顺序：

1. 定义 models 和 KV scopes。
2. 实现 memory core service。
3. 添加 REST routes。
4. 添加 CLI commands。
5. 添加单元、REST、CLI 测试。
