# llm-memory-processing Specification

## Purpose

定义 observation 写入后的 LLM summary、candidate memory 提炼、processing job 状态和审计能力。

## Requirements

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

### Requirement: Low-Frequency LLM Processing Trigger

系统 SHALL 将 observation LLM processing 作为低频阶段性动作使用。

Skill 或调用文档 MUST NOT 要求 agent 在每次工具调用、每次文件读取、每次编辑、每次命令执行或每次测试后调用 `observe`。未来 hook 高频采集入口 MUST NOT 默认同步触发 LLM processing。

#### Scenario: Stage summary observe

- **WHEN** agent 完成阶段性探索、修改、验证或复盘
- **THEN** Skill 可以指导 agent 调用 `observe` 触发 LLM processing

#### Scenario: Per-tool observe is disallowed

- **WHEN** agent 每次工具调用后都有原始事件
- **THEN** Skill 不得要求每个事件都同步调用 `observe` 并触发 LLM processing
