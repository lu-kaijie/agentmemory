## ADDED Requirements

### Requirement: Memory Scope Model
系统 SHALL 支持 Global 和 Project 两类记忆 scope。

所有长期 records MUST 能表达其作用域。Global records MUST 表达跨项目有效的用户偏好、通用规则、通用 lesson 或跨项目 insight。Project records MUST 绑定稳定 project identity。系统 MUST 避免默认把 Project records 注入其他项目 context。

#### Scenario: Save global memory
- **WHEN** 用户保存不绑定项目的长期偏好或通用经验
- **THEN** 系统保存为 global scope record

#### Scenario: Save project memory
- **WHEN** 用户在 project context 下保存 memory、knowledge、wiki page 或 insight
- **THEN** 系统保存为 project scope record，并关联 project identity

#### Scenario: Project context excludes other projects
- **WHEN** agent 请求某项目 context
- **THEN** 系统默认只包含 global records 和该项目 records

### Requirement: Project Entity
系统 SHALL 把 project 作为一等实体管理。

Project record MUST 包含 id、name、root、createdAt、updatedAt 和 metadata。系统 MUST 支持通过 observe、context、remember 或显式 project 命令自动创建或复用 project。Project identity MUST 稳定用于 search、context、Wiki、内部 session evidence 和 import/export。

#### Scenario: Upsert project from cwd
- **WHEN** 用户在项目目录下调用 context、observe 或 remember
- **THEN** 系统创建或复用对应 ProjectRecord，并把写入或查询关联到该 project

#### Scenario: List projects
- **WHEN** 用户请求 project 列表
- **THEN** 系统返回所有 ProjectRecord 及其基础 metadata

### Requirement: Default Project Resolution
系统 SHALL 在未显式传入 projectId 时从当前工作目录解析 project。

默认 resolver MUST 使用 `realpath(cwd)` 作为 project root，使用 root basename 作为 project name，并使用 root path fingerprint 生成稳定 project id。系统 MUST NOT 读取项目内 session/cache 文件作为 project 或 session 权威状态。系统 MUST NOT 仅使用 basename 作为唯一 project id。

#### Scenario: Resolve project from cwd
- **WHEN** 请求未提供 projectId 但提供 cwd
- **THEN** 系统根据 realpath(cwd) 创建或复用 ProjectRecord

#### Scenario: Same basename different roots
- **WHEN** 两个项目目录 basename 相同但 root path 不同
- **THEN** 系统生成不同 project ids

### Requirement: Internal Session Evidence
系统 SHALL 将 session 作为内部 evidence 容器，而不是用户必须管理的主模型。

`sessionId` MUST 继续支持显式传入。未传 `sessionId` 时，`observe` MAY 通过 project resolver 找到 project，并复用该 project 未超时的 internal current session；若不存在 current session 或 current session 超过配置 TTL，系统 MUST 自动创建新 session。`context` 和 `remember` MUST NOT 要求 sessionId。过期 session SHOULD 被标记 ended 或 stale，并尽量生成 summary。

Current session authority MUST 存在 AgentMemory 状态库中。系统 MUST NOT 使用 `.agentmemory/current-session.json` 作为权威 session 状态，因为 agent 可能被直接关闭而无法更新该文件。

#### Scenario: Reuse current session
- **WHEN** 同一 project 下已有未超时 active session 且请求未传 sessionId
- **THEN** 系统复用该 session

#### Scenario: Create current session
- **WHEN** 同一 project 下没有 active current session 且请求未传 sessionId
- **THEN** 系统自动创建 session 并记录为 project current session

#### Scenario: Expire stale current session
- **WHEN** current active session 超过配置 TTL
- **THEN** 系统结束或标记旧 session，并为新请求创建新 session

#### Scenario: End current session
- **WHEN** 用户运行 session end 且未传 sessionId
- **THEN** 系统结束当前 project 的 current active session

#### Scenario: Context does not require session
- **WHEN** 用户运行 context 且未传 sessionId
- **THEN** 系统按 Global + Project 生成 context，不要求存在 active session

### Requirement: Scoped Export And Import
系统 SHALL 在导出和导入时保留 memory scope 和 project identity。

Export MUST 包含 projects、scope 和 projectId。Import MUST 复用相同 project ids 或根据 root 合并项目。旧数据缺少 scope 时，系统 MUST 使用兼容默认值并在 import report 中记录。

#### Scenario: Export scoped records
- **WHEN** 用户导出数据
- **THEN** 导出 payload 包含 projects 和 records 的 scope/projectId

#### Scenario: Import legacy records
- **WHEN** 导入缺少 scope 的旧 records
- **THEN** 系统补默认 scope/project 并报告兼容迁移结果
