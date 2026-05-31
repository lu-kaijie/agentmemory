## ADDED Requirements

### Requirement: Scoped Search Filtering
系统 SHALL 支持按 scope、projectId 和 sessionId 检索。

Search request MUST 支持 scope/project/projectId/sessionId 过滤。Project context 默认搜索 MUST 包含 global records 和目标 project records，MUST 排除其他 project records。

#### Scenario: Search project with global fallback
- **WHEN** 用户按 project 搜索
- **THEN** 搜索结果包含 global records 和该 project records

#### Scenario: Search excludes other project
- **WHEN** 用户按 project 搜索
- **THEN** 搜索结果不包含其他 project records

### Requirement: Search Remains Evidence-Oriented
系统 SHALL 保持 search 为 evidence retrieval 接口。

Search MUST 返回结构化 results，不得默认用 LLM 重写为 synthesis。需要 LLM 组织答案时，用户 MUST 使用 smart-search 或 context。

#### Scenario: Search returns raw results
- **WHEN** 用户调用 search
- **THEN** 系统返回 sourceType、sourceId、content、score、matchSources 等原始检索字段
