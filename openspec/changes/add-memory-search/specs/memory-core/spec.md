## MODIFIED Requirements

### Requirement: Observation Save

系统 SHALL 保存 agent 工作过程 observation。

Observation MUST 包含 `id`、`sessionId`、`type`、`content`、`source`、`language`、`project`、`cwd`、`files`、`concepts` 和 `createdAt`。

Observation 保存成功后，系统 MUST 为 observation 创建 searchable document 并触发索引写入。索引写入失败 MUST NOT 回滚 observation 保存。

#### Scenario: Save observation

- **WHEN** agent 提交合法 observation payload
- **THEN** 系统保存 observation，并返回 observation id 和 session id

#### Scenario: Observation save triggers indexing

- **WHEN** 系统成功保存 observation
- **THEN** 系统为 observation 创建索引记录或记录 failed index job

### Requirement: Explicit Memory Save

系统 SHALL 保存用户明确要求保留的长期 memory。

Memory MUST 包含 `id`、`type`、`content`、`concepts`、`files`、`language`、`source` 和 `createdAt`。

Memory SHOULD 预留 `canonicalId`、`duplicateOf` 和 `relations` 字段，用于后续跨语言重复、补充、替代、冲突和相关关系治理。memory core 阶段 MUST NOT 自动合并跨语言相似 memory。

Memory 保存成功后，系统 MUST 为 memory 创建 searchable document 并触发索引写入。索引写入失败 MUST NOT 回滚 memory 保存。

#### Scenario: Save memory

- **WHEN** agent 提交合法 memory payload
- **THEN** 系统保存 memory，并返回 memory id

#### Scenario: Save multilingual duplicate candidate

- **WHEN** agent 保存一条与既有 memory 语义相近但语言不同的新 memory
- **THEN** memory core 保存新 memory，不自动删除或合并既有 memory

#### Scenario: Memory save triggers indexing

- **WHEN** 系统成功保存 memory
- **THEN** 系统为 memory 创建索引记录或记录 failed index job

### Requirement: Derived Memory Processing Data

系统 SHALL 支持列出 observation 派生的 summaries、candidate memories 和 LLM processing jobs。

Summary 保存成功后，系统 MUST 为 summary 创建 searchable document 并触发索引写入。索引写入失败 MUST NOT 回滚 summary 保存或 LLM processing job 状态。

#### Scenario: List summaries

- **WHEN** 客户端请求 summary 列表
- **THEN** 系统返回已保存 summaries

#### Scenario: List candidate memories

- **WHEN** 客户端请求 candidate memory 列表
- **THEN** 系统返回已保存 candidate memories

#### Scenario: List LLM processing jobs

- **WHEN** 客户端请求 LLM processing job 列表
- **THEN** 系统返回已保存 processing jobs

#### Scenario: Summary save triggers indexing

- **WHEN** 系统成功保存 summary
- **THEN** 系统为 summary 创建索引记录或记录 failed index job
