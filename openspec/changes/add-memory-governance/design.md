## Context

当前系统已经具备记忆写入、LLM 派生处理、关键词/向量检索、Skill 和 Viewer。缺口在治理：用户无法导出完整状态，也无法删除错误或过期的长期 memory。由于 memory 会进入 FTS5 和 LanceDB，删除不能只移除业务记录，还必须失效搜索文档和向量记录。

## Goals / Non-Goals

**Goals:**

- 提供完整 JSON 导出，便于用户备份、审计和迁移前检查。
- 提供按 memory id 精确删除能力。
- 删除 memory 后同步清理对应 searchable document、FTS5 记录、LanceDB 向量记录和相关索引状态。
- 为 export 和 forget 写入 audit。
- 通过 REST 和 CLI 提供等价入口。

**Non-Goals:**

- 不实现模糊删除、按 query 删除、批量删除或自动过期。
- 不实现 import。
- 不实现候选记忆接受/拒绝。
- 不在 Viewer 中提供删除按钮，避免第一版误操作。
- 不删除 observation、summary、candidate 或 audit 记录。

## Decisions

### 1. 删除仅支持 memory id 精确删除

`forget` 第一版只接受 `memoryId`。这样可以避免 query 删除、时间范围删除或批量删除带来的误删风险，也更容易让 agent 在执行前展示明确目标。

替代方案是支持按内容、概念或搜索结果删除，但这会把召回不确定性引入破坏性操作，暂不采用。

### 2. 删除保留 audit，不做硬清空历史

memory 删除后，系统写入 action 为 `forget` 的 audit。audit 记录只保存删除目标、来源、原因和最小必要快照，不重新暴露完整长期记忆列表。

替代方案是连 audit 一起删除，但这会破坏治理可追溯性。

### 3. 导出使用单一 JSON 对象

`export` 返回一个包含 `version`、`exportedAt` 和数据集合的 JSON 对象。集合覆盖当前本地状态，包括 sessions、observations、memories、summaries、memory candidates、LLM processing jobs、index jobs 和 audit。

导出不包含 LLM/embedding API key、运行时 secret 或 provider 密钥。provider 状态如需查看继续使用 health/doctor。

### 4. 索引删除走统一 helper

删除 memory 时通过 indexing helper 根据 `sourceType=memory` 和 `sourceId=<memoryId>` 清理：

- searchable document
- FTS5 记录
- LanceDB 向量记录
- pending/running/failed/done index job 的相关目标状态

如果 LanceDB 删除失败，业务删除仍返回结构化失败，不应让 memory 处于“业务已删但搜索仍可召回”的不一致成功状态。实现可以先删除索引再删除业务记录，或在失败时记录 failed audit 并返回错误。

### 5. CLI 与 REST 共用 core service

REST route 和 CLI command 都调用同一层 governance service，避免导出内容、删除行为和 audit 行为分叉。

## Risks / Trade-offs

- [Risk] LanceDB 删除 API 与当前表结构不匹配，导致向量记录残留。  
  Mitigation：新增测试覆盖删除后 vector/hybrid search 不返回该 memory，并在实现中封装单点删除 helper。

- [Risk] 导出数据过大。  
  Mitigation：第一版面向个人本地记忆，先返回完整 JSON；后续再做分页、流式导出或压缩文件。

- [Risk] 删除是破坏性操作。  
  Mitigation：第一版只支持精确 ID，不做批量和模糊删除；CLI 命令要求显式 `--memory-id`。

- [Risk] 导出 audit 本身写入 audit 会改变随后导出的 audit 列表。  
  Mitigation：导出流程先写 audit 再生成导出内容，保证导出文件包含本次 export 记录。
