## ADDED Requirements

### Requirement: Index Deletion On Memory Forget

系统 SHALL 在 memory 被 forget 时失效对应搜索索引。

系统 MUST 删除 `sourceType=memory` 且 `sourceId=<memoryId>` 的 searchable document、FTS5 记录和 LanceDB 向量记录。删除完成后，keyword、vector 和 hybrid search MUST NOT 返回被删除 memory。

#### Scenario: Forget removes keyword result

- **WHEN** 用户删除一个已被 FTS5 索引的 memory
- **THEN** 后续 keyword search 不返回该 memory

#### Scenario: Forget removes vector result

- **WHEN** 用户删除一个已被 LanceDB 索引的 memory
- **THEN** 后续 vector search 不返回该 memory

#### Scenario: Forget removes hybrid result

- **WHEN** 用户删除一个已被索引的 memory
- **THEN** 后续 hybrid search 不返回该 memory
