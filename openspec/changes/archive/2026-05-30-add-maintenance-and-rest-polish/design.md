## Context

当前服务启动时已有 index pending worker 和 wiki pending worker，但它们分散、配置有限，也没有统一的 maintenance 入口。失败任务主要靠手动 `index repair` 或重新触发 Wiki update。参考更完整的运行形态，长期运行系统应有 scheduled lifecycle、durable retry 和可观察的维护入口；当前项目先做轻量进程内版本。

## Goals / Non-Goals

**Goals:**

- 提供 `scripts/dev.sh`、`scripts/test.sh` 和 `.env.example`。
- 提供 `agentmemory maintenance run` 和 `POST /agentmemory/maintenance/run`。
- maintenance run 统一执行 index pending/failed repair、Wiki pending/failed retry，并返回摘要。
- FastAPI lifespan 启动一个可配置 maintenance loop。
- REST 可选返回 `{ status_code, body, headers? }` envelope，默认保持兼容。

**Non-Goals:**

- 不实现外部队列、分布式锁或 durable queue。
- 不实现复杂页面压缩算法，只为后续页面压缩保留 maintenance 结果字段。
- 不强制所有 REST 默认改 envelope，避免破坏现有测试和调用方。
- 不实现 Hook/MCP 自动接入。

## Decisions

- **轻量进程内 scheduler。** 使用 FastAPI lifespan 中的 asyncio task 定期调用 core maintenance；CLI/REST 可手动触发同一函数。
- **maintenance response 统一摘要。** 返回 index、wiki、llm、pageCompression、errors，便于 health/viewer 后续展示。
- **Wiki failed retry 通过重置 failed job 为 pending。** 复用现有 `process_wiki_updates`，避免复制处理逻辑。
- **LLM failed retry 保守处理。** failed LLM processing job 通过 observation id 找回 observation 重新处理，成功后写 summary/candidates/index/wiki/audit。
- **REST envelope opt-in。** 通过 `AGENTMEMORY_REST_ENVELOPE=true` 或 `?envelope=true` 返回统一响应格式，默认裸 JSON。

## Risks / Trade-offs

- **进程内调度不跨进程协调** → 第一版面向本地单服务；后续可换外部队列。
- **同步 maintenance 可能耗时** → limit 控制每轮处理数量，后台 interval 可配置。
- **LLM failed retry 可能重复候选** → 通过只重试 failed job，并更新同一 job，降低重复风险。
- **双响应格式增加测试面** → 默认兼容，新增 envelope 测试覆盖关键端点。
