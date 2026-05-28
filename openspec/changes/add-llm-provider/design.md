## Context

现有服务已经具备 FastAPI、Typer CLI、配置读取、SQLite `StateKV`、memory core 写入与基础审计。后续 RAG、LLM Wiki 和上下文压缩都需要 LLM 与 embedding 能力，但当前代码没有统一 provider 抽象，也没有区分 LLM 与 embedding 的独立配置。

本变更需要把 AI 调用能力纳入系统底座，同时保持本地开发可离线测试、API key 不泄露、provider 失败不影响 memory core 的基础写入能力。

## Goals / Non-Goals

**Goals:**

- 增加 LLM 与 embedding 的独立配置项。
- 定义 LLM provider 与 embedding provider 接口。
- 实现 fake provider，供测试和离线开发使用。
- 实现 OpenAI-compatible provider，支持自定义 base URL、API key 和 model。
- 在 `/agentmemory/health` 与 `agentmemory doctor` 中展示 provider 配置和可用性状态。
- Provider 调用失败时返回结构化错误，不影响已有 observe/remember/list 功能。

**Non-Goals:**

- 不把 observation 自动送入 LLM 摘要。
- 不提炼候选 memory。
- 不实现 FTS5、LanceDB、RAG search 或 embedding 索引写入。
- 不实现 Wiki 更新任务。
- 不实现复杂重试、限流、熔断或成本统计。

## Decisions

### 1. LLM 与 Embedding 独立配置

新增配置分组：

- LLM：`AGENTMEMORY_LLM_PROVIDER`、`AGENTMEMORY_LLM_BASE_URL`、`AGENTMEMORY_LLM_API_KEY`、`AGENTMEMORY_LLM_MODEL`
- Embedding：`AGENTMEMORY_EMBEDDING_PROVIDER`、`AGENTMEMORY_EMBEDDING_BASE_URL`、`AGENTMEMORY_EMBEDDING_API_KEY`、`AGENTMEMORY_EMBEDDING_MODEL`

`provider` 支持 `fake` 和 `openai`。fake 是默认值，保证本地无 API key 也能运行测试；openai 使用 OpenAI-compatible HTTP API。

### 2. Provider 接口保持同步、窄边界

P0 使用同步接口，和当前 FastAPI/CLI 代码风格一致，降低实现复杂度。接口包括：

- `summarize(text, instruction=None)`
- `extract_memories(text)`
- `explain_search(query, results)`
- `compress_context(items, token_budget)`
- `update_wiki(page_title, current_content, evidence)`
- `embed_texts(texts)`

这些方法先建立调用边界，后续 RAG/Wiki change 再决定何时调用、如何入库。

### 3. Fake Provider 用确定性输出

Fake LLM 不模拟复杂智能，只返回稳定、可断言的字符串或结构化结果。Fake embedding 对同样文本返回稳定向量，便于单元测试和后续索引测试。

### 4. OpenAI-compatible Provider 使用官方 SDK

使用 `openai` Python SDK 的 OpenAI-compatible client。LLM 使用 chat completions 或 responses 的可用兼容接口；embedding 使用 embeddings endpoint。API key 只从配置读取，健康检查只报告是否配置，不返回 key 明文。

### 5. 健康检查做轻量状态，不强制真实远程探测

`/agentmemory/health` 和 `doctor` 展示 provider 名称、模型名、是否缺少 API key、最近错误。为避免健康检查变慢或产生费用，默认不调用远程 LLM。CLI 可提供显式 probe 选项或在 doctor 中做本地配置校验。

## Risks / Trade-offs

- OpenAI-compatible 服务差异较大 -> 先封装在 provider 内部，外部只依赖接口和结构化错误。
- 健康检查不真实调用远程服务可能无法发现网络问题 -> 通过最近错误和后续显式 probe 弥补。
- Fake embedding 不能代表真实语义效果 -> 只用于测试稳定性，不作为产品效果依据。
- 同步调用在高并发场景下不够理想 -> 当前是本地个人服务，后续如果需要后台任务和并发处理再引入 async。

## Migration Plan

无数据迁移。

实施顺序：

1. 扩展配置模型和 safe summary。
2. 新增 provider 模型、接口和 fake 实现。
3. 新增 OpenAI-compatible 实现。
4. 增加 provider factory 和健康状态方法。
5. 扩展 API health 与 CLI doctor。
6. 添加配置、fake provider、OpenAI provider 构造和健康输出测试。
