## Why

AgentMemory 已经支持完整治理导出，但缺少对应的导入恢复能力。长期记忆数据需要能在新库、备份恢复和版本迁移场景中重新导入，并保持可搜索、可审计和可验证。

## What Changes

- 增加治理导入能力，支持读取 export JSON 并恢复 sessions、observations、memories、summaries、memory candidates、LLM jobs、knowledge、Wiki pages、Wiki jobs、index jobs 和 audit。
- 明确 export/import payload 的兼容版本字段和基础兼容校验。
- 导入时执行结构校验、版本校验和保守去重，避免重复写入同一 id。
- 导入完成后触发或补建搜索索引，使 memory、summary、knowledge 和 Wiki page 可被 search/context 使用。
- 导入行为写入 audit，记录来源、版本、导入数量、跳过数量和错误摘要。
- 增加 CLI 和 REST 入口：`agentmemory import --file <path> --json`、`POST /agentmemory/import`。

## Capabilities

### New Capabilities

### Modified Capabilities

- `memory-governance`: 增加治理导入、版本兼容校验、去重和 import audit 要求。
- `memory-core-interfaces`: 增加 import CLI 和 REST 接口要求。

## Impact

- 影响 core models、service、CLI、REST API、search/index repair 和测试。
- 影响 `PROJECT.md`、Skill 文档和 OpenSpec 大任务进度。
- 不引入新外部依赖，不改变现有 export、forget、search 或 context 调用兼容性。
