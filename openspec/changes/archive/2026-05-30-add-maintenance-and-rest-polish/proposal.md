## Why

AgentMemory 的核心记忆链路已经可用，但还缺少一组让本地开发、失败恢复、REST 调用和长期运行更稳定的工程化能力。需要补齐本地脚本、重试入口、统一 REST 响应和轻量后台维护调度。

## What Changes

- 增加本地开发脚本、测试脚本和 `.env.example`，降低启动和验收成本。
- 增加 maintenance 能力，统一处理 pending/failed index jobs、pending/failed Wiki jobs 和基础 repair。
- 增加 CLI/REST 入口用于手动运行 maintenance 和重试失败任务。
- 增加可配置后台 maintenance loop，服务运行时按间隔自动处理 pending/failed jobs。
- REST 支持统一响应 envelope `{ status_code, body, headers? }`，同时保留现有裸 JSON 兼容默认行为。
- 更新 health/config 输出，让维护调度状态可见。

## Capabilities

### New Capabilities

### Modified Capabilities

- `python-service-foundation`: 增加本地开发脚本、测试脚本、示例环境和后台调度配置。
- `llm-memory-processing`: 增加失败 LLM processing job 的重试入口要求。
- `memory-indexing`: 增加 failed/pending index job 的维护调度和重试要求。
- `memory-wiki`: 增加 Wiki update job 合并、失败重试和维护调度要求。
- `memory-core-interfaces`: 增加 maintenance CLI/REST 和可选统一 REST response envelope 要求。

## Impact

- 影响配置、API app lifespan、core service、search service、CLI、REST、health、项目脚本和测试。
- 不引入外部队列或 cron 依赖；第一版使用进程内维护 loop 和显式 CLI/REST 入口。
- 不改变现有 REST 默认响应兼容性；统一 envelope 通过配置或 query 参数启用。
