## ADDED Requirements

### Requirement: Derived Memory Processing Data

系统 SHALL 支持列出 observation 派生的 summaries、candidate memories 和 LLM processing jobs。

#### Scenario: List summaries

- **WHEN** 客户端请求 summary 列表
- **THEN** 系统返回已保存 summaries

#### Scenario: List candidate memories

- **WHEN** 客户端请求 candidate memory 列表
- **THEN** 系统返回已保存 candidate memories

#### Scenario: List LLM processing jobs

- **WHEN** 客户端请求 LLM processing job 列表
- **THEN** 系统返回已保存 processing jobs
