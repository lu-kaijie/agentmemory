## ADDED Requirements

### Requirement: Full Data Export

系统 SHALL 支持导出 AgentMemory 当前完整可治理数据。

Export payload MUST 包含 `version`、`exportedAt`、`sessions`、`observations`、`memories`、`summaries`、`memoryCandidates`、`llmProcessingJobs`、`indexJobs` 和 `audit`。Export payload MUST NOT 包含 LLM API key、embedding API key 或 `AGENTMEMORY_SECRET` 明文。

#### Scenario: Export complete governance data

- **WHEN** 用户触发 export
- **THEN** 系统返回包含 sessions、observations、memories、summaries、memory candidates、LLM processing jobs、index jobs 和 audit 的 JSON 对象

#### Scenario: Export redacts secrets

- **WHEN** 系统已配置 LLM、embedding 或 REST secret
- **THEN** export payload 不包含任何密钥明文

### Requirement: Export Audit

系统 MUST 为成功导出写入 audit。

Export audit MUST 使用 action `export`，targetType `governance`，并记录导出来源和导出集合摘要。

#### Scenario: Successful export writes audit

- **WHEN** 用户成功导出数据
- **THEN** 系统写入 action 为 `export` 的 audit 记录

### Requirement: Explicit Memory Forget

系统 SHALL 支持按 memory id 精确删除用户显式保存的长期 memory。

Forget request MUST 指定 `memoryId`。系统 MUST NOT 在第一版支持模糊删除、按 query 删除或批量删除。删除不存在的 memory MUST 返回结构化错误，并且 MUST NOT 写入成功 forget audit。

#### Scenario: Forget memory by id

- **WHEN** 用户提交存在的 memory id
- **THEN** 系统删除该 memory
- **AND** 后续 memories 列表不再返回该 memory

#### Scenario: Reject missing memory id

- **WHEN** 用户提交不存在的 memory id
- **THEN** 系统返回结构化 not found 错误
- **AND** 不写入成功 forget audit

### Requirement: Forget Audit

系统 MUST 为成功 memory 删除写入 audit。

Forget audit MUST 使用 action `forget`，targetType `memory`，targetId 为被删除 memory id，并记录 source、reason 和必要 details。

#### Scenario: Successful forget writes audit

- **WHEN** 用户成功删除 memory
- **THEN** 系统写入 action 为 `forget` 的 audit 记录
