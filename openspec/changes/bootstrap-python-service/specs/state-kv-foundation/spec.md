## ADDED Requirements

### Requirement: SQLite StateKV Storage

系统 SHALL 提供 SQLite-backed `StateKV` 基础状态层。

`StateKV` MUST 支持 `get`、`set`、`delete` 和 `list` 操作，并以 `scope` 和 `key` 区分不同状态域。

#### Scenario: Set and get value

- **WHEN** 调用 `StateKV.set(scope, key, value)` 后再调用 `StateKV.get(scope, key)`
- **THEN** 系统返回之前保存的 JSON 值

#### Scenario: List scope values

- **WHEN** 同一 scope 下保存多条记录
- **THEN** `StateKV.list(scope)` 返回该 scope 下的记录集合

#### Scenario: Delete value

- **WHEN** 调用 `StateKV.delete(scope, key)`
- **THEN** 后续 `StateKV.get(scope, key)` 返回空结果

### Requirement: StateKV Timestamps

系统 SHALL 为每条 KV 记录维护创建时间和更新时间。

#### Scenario: Updating value changes updated timestamp

- **WHEN** 同一 scope/key 被再次写入
- **THEN** 系统保留记录并更新 `updated_at`

### Requirement: StateKV Database Initialization

系统 SHALL 在首次使用 `StateKV` 时初始化所需 SQLite 表。

#### Scenario: New database initializes schema

- **WHEN** 使用一个不存在的 SQLite 文件创建 `StateKV`
- **THEN** 系统创建数据库文件和 KV 表
