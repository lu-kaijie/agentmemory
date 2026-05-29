# llm-provider Specification

## Purpose
TBD - created by archiving change add-llm-provider. Update Purpose after archive.
## Requirements
### Requirement: Provider Configuration

系统 SHALL 支持 LLM 与 embedding 的独立 provider 配置。

系统 MUST 使用 OpenAI-compatible provider。LLM 与 embedding MUST 分别支持 base URL、API key 和 model 配置。系统 MUST 在配置摘要中隐藏 API key 明文。

#### Scenario: Missing provider configuration blocks startup

- **WHEN** 用户未配置 LLM 或 embedding provider
- **THEN** 系统拒绝进入可用运行状态，并报告缺失配置

#### Scenario: OpenAI-compatible provider configuration

- **WHEN** 用户配置 OpenAI-compatible base URL、API key 和 model
- **THEN** 系统创建对应 provider，并在配置摘要中只显示是否已配置 API key

### Requirement: LLM Provider Interface

系统 SHALL 提供统一 LLM provider 接口。

接口 MUST 覆盖摘要、记忆提炼、搜索解释、上下文压缩和 Wiki 更新的调用边界。provider 调用失败 MUST 返回或抛出结构化错误，调用方能够记录最近错误。

Search explanation MUST 只基于调用方传入的 search results/evidence 生成，不得编造未在 evidence 中出现的事实。

#### Scenario: Summarize text

- **WHEN** 调用方请求 provider 摘要文本
- **THEN** provider 返回摘要文本或结构化错误

#### Scenario: Extract memory candidates

- **WHEN** 调用方请求 provider 从文本中提炼候选记忆
- **THEN** provider 只解析 XML-like `<memory>` 标签中的候选记忆，并返回候选记忆列表或结构化错误

#### Scenario: Compress context

- **WHEN** 调用方请求 provider 按 token budget 压缩上下文
- **THEN** provider 返回压缩后的上下文文本或结构化错误

#### Scenario: Explain search results

- **WHEN** 调用方请求 provider 解释 search results
- **THEN** provider 返回基于 evidence 的解释或结构化错误

### Requirement: Embedding Provider Interface

系统 SHALL 提供统一 embedding provider 接口。

接口 MUST 支持对一组文本生成 embedding 向量。返回结果 MUST 保持与输入文本顺序一致。

#### Scenario: Embed multiple texts

- **WHEN** 调用方提交多段文本
- **THEN** provider 返回同等数量且顺序一致的 embedding 向量

### Requirement: OpenAI-Compatible Providers

系统 SHALL 提供 OpenAI-compatible LLM provider 和 embedding provider。

OpenAI-compatible provider MUST 使用配置中的 base URL、API key 和 model。缺少必要配置时，系统 MUST 阻止服务进入可用运行状态，并且 MUST NOT 泄露密钥。

#### Scenario: Missing OpenAI API key

- **WHEN** LLM 或 embedding API key 为空
- **THEN** 系统启动失败，并说明缺少 API key

#### Scenario: Create OpenAI-compatible clients

- **WHEN** LLM 与 embedding 的必要配置完整
- **THEN** 系统可以创建 LLM 与 embedding provider 实例
