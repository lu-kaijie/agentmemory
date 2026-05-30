## ADDED Requirements

### Requirement: LLM Processing Retry

系统 SHALL 支持重试 failed LLM processing jobs。

Retry MUST 基于原始 observation 重新执行 summary 和 candidate memory extraction。成功后 MUST 更新同一个 job 的 status、summaryId、candidateIds、lastError 和 finishedAt，并写入 summary、candidate memories、search index、Wiki update job 和 audit。失败时 MUST 保留 failed 状态并更新 attempts、lastError 和 finishedAt。

#### Scenario: Retry failed LLM job succeeds

- **WHEN** maintenance 或显式重试处理 failed LLM processing job 且 LLM 调用成功
- **THEN** 系统将该 job 标记为 done 并保存派生数据

#### Scenario: Retry failed LLM job fails again

- **WHEN** maintenance 或显式重试处理 failed LLM processing job 且 LLM 调用失败
- **THEN** 系统保留 failed 状态并记录最新 lastError
