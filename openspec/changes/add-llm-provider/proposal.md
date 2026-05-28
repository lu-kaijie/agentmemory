## Why

当前系统已经可以保存 observation、memory 和 audit，但还没有可配置的 LLM 与 embedding 能力。作为 AI native 个人长期记忆产品，后续摘要、候选记忆提炼、智能检索、上下文压缩和 Wiki 更新都需要先有稳定的 provider 底座。

本变更先建立 OpenAI-compatible LLM/Embedding provider、离线 fake provider 和配置/健康检查能力，为后续 RAG 与 LLM Wiki 提供基础设施。

## What Changes

- 新增 LLM provider 接口，覆盖摘要、记忆提炼、搜索解释、上下文压缩和 Wiki 更新的调用边界。
- 新增 embedding provider 接口，支持文本向量生成。
- 新增 fake LLM provider 与 fake embedding provider，用于本地测试和无网络开发。
- 新增 OpenAI-compatible LLM provider，支持独立配置 base URL、API key 和 model。
- 新增 OpenAI-compatible embedding provider，支持独立配置 base URL、API key 和 model。
- 扩展配置读取与敏感值隐藏规则，避免健康检查泄露 API key。
- 扩展 `doctor` 与 `/agentmemory/health`，展示 LLM/embedding 配置状态、模型名和最近错误。
- 不实现 RAG 索引、向量数据库写入、智能检索、自动摘要入库或 Wiki 更新任务。

## Capabilities

### New Capabilities

- `llm-provider`: LLM 与 embedding provider 的配置、接口、fake 实现、OpenAI-compatible 实现和可用性检查。

### Modified Capabilities

- `memory-core-interfaces`: 健康检查和 doctor 输出增加 LLM/embedding provider 状态，但不改变 memory core 写入接口。

## Impact

- 新增 provider 模块、配置字段、测试和 OpenAI SDK 依赖。
- 修改健康检查响应和 CLI `doctor` 输出。
- 后续 `add-rag-search` 可以直接复用 embedding provider，`add-llm-wiki` 可以直接复用 LLM provider。
