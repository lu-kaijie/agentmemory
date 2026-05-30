## ADDED Requirements

### Requirement: Wiki Maintenance Retry And Merge

系统 SHALL 通过 maintenance 入口处理 pending 和 failed Wiki update jobs。

Maintenance MUST 支持将 failed Wiki jobs 重置为 pending 并重试。系统 SHOULD 合并相同 topic 且 sourceIds 重叠的 pending Wiki jobs，减少重复 LLM 调用。Maintenance response MUST 返回处理的 Wiki jobs、updated pages、distilled knowledge 和错误信息。

#### Scenario: Maintenance retries failed wiki job

- **WHEN** 存在 failed Wiki update job
- **THEN** maintenance run 将其重试并返回处理结果

#### Scenario: Maintenance processes pending wiki jobs

- **WHEN** 存在 pending Wiki update job
- **THEN** maintenance run 处理这些 job 并返回处理结果
