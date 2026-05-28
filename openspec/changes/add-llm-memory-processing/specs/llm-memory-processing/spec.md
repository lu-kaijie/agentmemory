## ADDED Requirements

### Requirement: Observation LLM Summary

系统 SHALL 在 observation 保存后使用 LLM 生成 summary。

Summary MUST 包含 `id`、`observationId`、`content`、`source`、`language` 和 `createdAt`。

#### Scenario: Generate summary after observe

- **WHEN** agent 提交合法 observation payload
- **THEN** 系统保存 observation，并使用 LLM 生成 summary

### Requirement: Candidate Memory Extraction

系统 SHALL 在 observation 保存后使用 LLM 提炼 candidate memories。

Candidate memory MUST 包含 `id`、`observationId`、`content`、`type`、`confidence`、`concepts`、`files`、`language`、`status` 和 `createdAt`。Candidate memory MUST NOT 自动保存为正式 memory。

#### Scenario: Extract candidate memories

- **WHEN** LLM 从 observation 中提炼出长期记忆候选
- **THEN** 系统保存 candidate memories，并保持正式 memories 列表不变

### Requirement: LLM Processing Jobs

系统 SHALL 为每次 observation LLM processing 保存 job 状态。

Job MUST 包含 `id`、`observationId`、`status`、`summaryId`、`candidateIds`、`lastError`、`startedAt` 和 `finishedAt`。Status MUST 支持 `running`、`done` 和 `failed`。

#### Scenario: Processing succeeds

- **WHEN** summary 和 candidate memory extraction 都成功
- **THEN** 系统将 job 标记为 `done`，并记录 summaryId 和 candidateIds

#### Scenario: Processing fails

- **WHEN** LLM processing 调用失败
- **THEN** 系统保留 observation，将 job 标记为 `failed`，并记录 lastError

### Requirement: LLM Processing Audit

系统 SHALL 为 LLM processing 成功和失败写入 audit。

Audit action MUST 区分 `llm_processing_done` 和 `llm_processing_failed`。

#### Scenario: Processing success writes audit

- **WHEN** LLM processing 成功完成
- **THEN** 系统写入 action 为 `llm_processing_done` 的 audit 记录

#### Scenario: Processing failure writes audit

- **WHEN** LLM processing 失败
- **THEN** 系统写入 action 为 `llm_processing_failed` 的 audit 记录
