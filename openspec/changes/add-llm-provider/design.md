## Context

现有服务已经具备 FastAPI、Typer CLI、配置读取、SQLite `StateKV`、memory core 写入与基础审计。后续 RAG、LLM Wiki 和上下文压缩都需要 LLM 与 embedding 能力，但当前代码没有统一 provider 抽象，也没有区分 LLM 与 embedding 的独立配置。

本变更需要把 AI 调用能力纳入系统底座，并把可用 AI provider 作为系统运行前提。API key 不能泄露；provider 配置缺失时系统必须尽早失败，而不是退回到非 AI 模式。

## Goals / Non-Goals

**Goals:**

- 增加 LLM 与 embedding 的独立配置项。
- 定义 LLM provider 与 embedding provider 接口。
- 实现 OpenAI-compatible provider，支持自定义 base URL、API key 和 model。
- 在 `/agentmemory/health` 与 `agentmemory doctor` 中展示 provider 配置和可用性状态。
- Provider 配置缺失时阻止服务进入可用状态。
- Provider 调用失败时返回结构化错误并记录最近错误。

**Non-Goals:**

- 不把 observation 自动送入 LLM 摘要。
- 不提炼候选 memory。
- 不实现 FTS5、LanceDB、RAG search 或 embedding 索引写入。
- 不实现 Wiki 更新任务。
- 不实现 fake、mock 或离线 provider，包括测试运行模式。
- 不实现复杂重试、限流、熔断或成本统计。

## Decisions

### 1. LLM 与 Embedding 独立必需配置

新增配置分组：

- LLM：`AGENTMEMORY_LLM_BASE_URL`、`AGENTMEMORY_LLM_API_KEY`、`AGENTMEMORY_LLM_MODEL`
- Embedding：`AGENTMEMORY_EMBEDDING_BASE_URL`、`AGENTMEMORY_EMBEDDING_API_KEY`、`AGENTMEMORY_EMBEDDING_MODEL`

provider 固定为 OpenAI-compatible。LLM 与 embedding 可以使用不同的 base URL、API key 和 model。任意必需配置缺失时，配置校验失败，`serve` 不启动；`doctor` 显示具体缺失项并返回失败。

### 2. Provider 接口保持同步、窄边界

P0 使用同步接口，和当前 FastAPI/CLI 代码风格一致，降低实现复杂度。接口包括：

- `summarize(text, instruction=None)`
- `extract_memories(text)`
- `explain_search(query, results)`
- `compress_context(items, token_budget)`
- `update_wiki(page_title, current_content, evidence)`
- `embed_texts(texts)`

这些方法先建立调用边界，后续 RAG/Wiki change 再决定何时调用、如何入库。

### 3. OpenAI-compatible Provider 使用官方 SDK

使用 `openai` Python SDK 的 OpenAI-compatible client。LLM 使用 chat completions 或 responses 的可用兼容接口；embedding 使用 embeddings endpoint。API key 只从配置读取，健康检查只报告是否配置，不返回 key 明文。

测试使用真实 OpenAI-compatible 服务。运行测试前必须配置 LLM 与 embedding 的 base URL、API key 和 model；缺少配置时相关测试失败，提醒先完成配置。

### 4. 启动时强校验，健康检查做状态展示

服务创建时校验 LLM 与 embedding 配置完整性。缺少配置时，`agentmemory serve` 失败退出；直接创建 API app 也失败，避免系统在无 AI 状态下继续写入数据。

`/agentmemory/health` 展示 provider 名称、模型名、密钥是否已配置、ready 状态和最近错误。为避免健康检查变慢或产生费用，默认不调用远程 LLM。`agentmemory doctor` 可以在配置缺失时输出缺失项并以非零退出码结束。

## Risks / Trade-offs

- OpenAI-compatible 服务差异较大 -> 先封装在 provider 内部，外部只依赖接口和结构化错误。
- 健康检查不真实调用远程服务可能无法发现网络问题 -> 通过最近错误和后续显式 probe 弥补。
- 本地开发和测试必须配置真实或兼容的 AI 服务 -> 符合 AI native 产品约束，但会提高开发门槛并引入网络/API 成本。
- 同步调用在高并发场景下不够理想 -> 当前是本地个人服务，后续如果需要后台任务和并发处理再引入 async。

## Migration Plan

无数据迁移。

实施顺序：

1. 扩展配置模型和 safe summary。
2. 新增 provider 模型和接口。
3. 新增 OpenAI-compatible 实现。
4. 增加 provider factory 和健康状态方法。
5. 扩展 API health 与 CLI doctor。
6. 添加配置校验、OpenAI provider 真实调用、缺失配置失败和健康输出测试。
