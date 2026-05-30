## ADDED Requirements

### Requirement: Index Maintenance Retry

系统 SHALL 通过 maintenance 入口处理 pending 和 failed index jobs。

Maintenance MUST 复用 index repair 或等价逻辑，补建缺失 searchable documents，并重试 failed 或 pending embedding jobs。Maintenance response MUST 返回处理的 documents 数、jobs 摘要和错误信息。

#### Scenario: Maintenance retries failed index job

- **WHEN** 存在 failed index job
- **THEN** maintenance run 重试该 job

#### Scenario: Maintenance repairs missing searchable document

- **WHEN** 源数据存在但 searchable document 缺失
- **THEN** maintenance run 补建 searchable document 并创建或处理 index job
