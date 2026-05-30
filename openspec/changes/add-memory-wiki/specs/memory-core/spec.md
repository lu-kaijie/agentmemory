## ADDED Requirements

### Requirement: Wiki Core List Data

系统 SHALL 支持列出 Wiki pages 和 Wiki update jobs。

#### Scenario: List wiki pages from core

- **WHEN** 调用方请求 Wiki page 列表
- **THEN** core service 返回已保存 Wiki pages

#### Scenario: List wiki update jobs from core

- **WHEN** 调用方请求 Wiki update job 列表
- **THEN** core service 返回已保存 Wiki update jobs
