## MODIFIED Requirements

### Requirement: Governance REST API

系统 SHALL 通过 REST API 暴露 memory governance 能力。

P0 MUST 提供：

- `GET /agentmemory/export`
- `POST /agentmemory/import`
- `POST /agentmemory/forget`

`POST /agentmemory/import` MUST 接受 AgentMemory export JSON payload。`POST /agentmemory/forget` MUST 接受 `memoryId` 和可选 `reason`。REST import response MUST 返回 imported/skipped/errors 摘要和 audit id。REST forget response MUST 返回被删除 memory id 和 audit id。

#### Scenario: REST export

- **WHEN** 客户端请求 `/agentmemory/export`
- **THEN** 系统返回完整治理导出 JSON

#### Scenario: REST import

- **WHEN** 客户端向 `/agentmemory/import` 提交合法 export JSON
- **THEN** 系统导入数据并返回 imported/skipped/errors 摘要和 audit id

#### Scenario: REST forget memory

- **WHEN** 客户端向 `/agentmemory/forget` 提交存在的 memory id
- **THEN** 系统删除 memory 并返回 memory id 和 audit id

### Requirement: Governance CLI

系统 SHALL 通过 CLI 暴露 memory governance 能力。

P0 MUST 提供：

- `agentmemory export`
- `agentmemory import --file <path>`
- `agentmemory forget --memory-id <id>`

`agentmemory export` MUST 支持 `--json`。`agentmemory import` MUST 支持 `--json` 并从指定 JSON 文件读取 AgentMemory export payload。`agentmemory forget` MUST 支持可选 `--reason`，并在成功时输出被删除 memory id 和 audit id。

#### Scenario: CLI export json

- **WHEN** 用户运行 `agentmemory export --json`
- **THEN** CLI 输出完整治理导出 JSON

#### Scenario: CLI import json

- **WHEN** 用户运行 `agentmemory import --file <path> --json`
- **THEN** CLI 导入文件中的 export JSON 并输出 imported/skipped/errors 摘要和 audit id

#### Scenario: CLI forget memory

- **WHEN** 用户运行 `agentmemory forget --memory-id <id>`
- **THEN** CLI 删除对应 memory 并输出删除结果
