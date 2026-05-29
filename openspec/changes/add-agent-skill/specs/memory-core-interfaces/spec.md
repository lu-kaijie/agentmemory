## ADDED Requirements

### Requirement: Skill-Compatible CLI Output

系统 SHALL 保持 AgentMemory CLI 适合 Skill 驱动的 agent 调用。

查询类 CLI 命令 MUST 支持 `--json`，写入类 CLI 命令 SHOULD 提供可解析的成功标识。Skill MUST 以当前已实现 CLI 命令为准，不引用未实现命令。

#### Scenario: Agent parses query output

- **WHEN** agent 按 Skill 调用查询类 CLI 命令并传入 `--json`
- **THEN** CLI 返回结构化 JSON

### Requirement: Skill-Compatible REST Fallback

系统 SHALL 保持 REST API 可作为 Skill 的兜底调用入口。

Skill 中列出的 REST 路径 MUST 对应当前已实现接口。REST 响应 MUST 包含 agent 可追踪的 source ids、job ids 或实体 ids。

#### Scenario: Agent falls back to REST API

- **WHEN** agent 无法使用 CLI 但可以调用本地 HTTP 服务
- **THEN** agent 可以按 Skill 调用 REST API 完成等价操作
