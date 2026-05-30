## MODIFIED Requirements

### Requirement: Full Data Export

系统 SHALL 支持导出 AgentMemory 当前完整可治理数据。

Export payload MUST 包含 `version`、`schemaVersion`、`exportedAt`、`sessions`、`observations`、`memories`、`summaries`、`memoryCandidates`、`llmProcessingJobs`、`knowledge`、`wikiPages`、`wikiUpdateJobs`、`indexJobs` 和 `audit`。`schemaVersion` MUST 表示治理 payload schema 版本。Export payload MUST NOT 包含 LLM API key、embedding API key 或 `AGENTMEMORY_SECRET` 明文。

#### Scenario: Export complete governance data

- **WHEN** 用户触发 export
- **THEN** 系统返回包含 sessions、observations、memories、summaries、memory candidates、LLM processing jobs、knowledge、Wiki pages、Wiki jobs、index jobs 和 audit 的 JSON 对象

#### Scenario: Export includes schema version

- **WHEN** 用户触发 export
- **THEN** export payload 包含当前治理 schemaVersion

#### Scenario: Export redacts secrets

- **WHEN** 系统已配置 LLM、embedding 或 REST secret
- **THEN** export payload 不包含任何密钥明文

## ADDED Requirements

### Requirement: Full Data Import

系统 SHALL 支持导入 AgentMemory export JSON。

Import payload MUST 是 AgentMemory governance export 格式。系统 MUST 校验 `schemaVersion` 或兼容的 `version` 字段。第一版 MUST 支持 `schemaVersion=1`，并 MUST 将缺失 `schemaVersion` 但包含合法 `version` 的当前导出按 schema 1 处理。系统 MUST 恢复 sessions、observations、memories、summaries、memory candidates、LLM jobs、knowledge、Wiki pages、Wiki jobs、index jobs 和历史 audit。

#### Scenario: Import exported data

- **WHEN** 用户导入合法 export JSON
- **THEN** 系统恢复 payload 中的治理数据集合

#### Scenario: Reject unsupported import version

- **WHEN** 用户导入不支持的 schemaVersion
- **THEN** 系统拒绝导入并返回结构化错误

#### Scenario: Import current export without schema version

- **WHEN** 用户导入缺失 schemaVersion 但包含合法 version 的当前 export JSON
- **THEN** 系统按 schema 1 兼容处理

### Requirement: Import Deduplication And Validation

系统 SHALL 在导入时执行基础结构校验和保守去重。

系统 MUST 按 record id 检查每个目标集合。目标库已有相同 id 时 MUST 跳过该记录，MUST NOT 覆盖已有数据。单条记录校验失败时系统 SHOULD 跳过该记录并记录错误；payload 版本或顶层结构不合法时 MUST 拒绝整个导入。

Import response MUST 返回 `imported`、`skipped`、`errors` 和 `auditId`。

#### Scenario: Skip existing record id

- **WHEN** 导入 payload 中某条 record id 已存在
- **THEN** 系统跳过该 record 且不覆盖现有数据

#### Scenario: Report invalid record

- **WHEN** 导入 payload 中某条 record 字段不合法
- **THEN** 系统跳过该 record 并在 errors 中报告

### Requirement: Import Index Repair

系统 SHALL 在导入成功后确保可检索数据进入索引。

导入 observations、memories、summaries、knowledge 或 Wiki pages 后，系统 MUST 为这些数据创建或修复 searchable documents。导入完成后，search 和 context MUST 能检索到已恢复的可检索数据。

#### Scenario: Imported memory is searchable

- **WHEN** 用户导入包含 memory 的 export JSON
- **THEN** 导入完成后 search 能返回该 memory

#### Scenario: Imported wiki is usable by context

- **WHEN** 用户导入包含 Wiki page 或 knowledge 的 export JSON
- **THEN** context 能使用导入后的 evidence

### Requirement: Import Audit

系统 MUST 为成功 import 写入 audit。

Import audit MUST 使用 action `import`，targetType `governance`，targetId 为 `agentmemory`，并记录 source、schemaVersion、imported、skipped 和 errors 摘要。

#### Scenario: Successful import writes audit

- **WHEN** 用户成功导入数据
- **THEN** 系统写入 action 为 `import` 的 audit 记录
