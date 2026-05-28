## ADDED Requirements

### Requirement: Provider Configuration

系统 SHALL 支持 LLM 与 embedding 的独立 provider 配置。

配置 MUST 支持 `fake` 和 `openai` provider。LLM 与 embedding MUST 分别支持 base URL、API key 和 model 配置。系统 MUST 在配置摘要中隐藏 API key 明文。

#### Scenario: Fake provider default

- **WHEN** 用户未配置 LLM 或 embedding provider
- **THEN** 系统使用 fake provider，并且服务可以正常启动

#### Scenario: OpenAI-compatible provider configuration

- **WHEN** 用户配置 OpenAI-compatible base URL、API key 和 model
- **THEN** 系统创建对应 provider，并在配置摘要中只显示是否已配置 API key

### Requirement: LLM Provider Interface

系统 SHALL 提供统一 LLM provider 接口。

接口 MUST 覆盖摘要、记忆提炼、搜索解释、上下文压缩和 Wiki 更新的调用边界。provider 调用失败 MUST 返回或抛出结构化错误，调用方能够记录最近错误。

#### Scenario: Summarize text

- **WHEN** 调用方请求 provider 摘要文本
- **THEN** provider 返回摘要文本或结构化错误

#### Scenario: Extract memory candidates

- **WHEN** 调用方请求 provider 从文本中提炼候选记忆
- **THEN** provider 返回候选记忆列表或结构化错误

#### Scenario: Compress context

- **WHEN** 调用方请求 provider 按 token budget 压缩上下文
- **THEN** provider 返回压缩后的上下文文本或结构化错误

### Requirement: Embedding Provider Interface

系统 SHALL 提供统一 embedding provider 接口。

接口 MUST 支持对一组文本生成 embedding 向量。返回结果 MUST 保持与输入文本顺序一致。

#### Scenario: Embed multiple texts

- **WHEN** 调用方提交多段文本
- **THEN** provider 返回同等数量且顺序一致的 embedding 向量

### Requirement: Fake Providers

系统 SHALL 提供 fake LLM provider 和 fake embedding provider。

Fake provider MUST 输出稳定结果，以支持离线开发和单元测试。

#### Scenario: Fake LLM deterministic output

- **WHEN** 使用 fake LLM provider 对同一输入调用摘要或记忆提炼
- **THEN** 系统返回稳定、可断言的结果

#### Scenario: Fake embedding deterministic output

- **WHEN** 使用 fake embedding provider 对同一文本生成 embedding
- **THEN** 系统返回稳定且维度固定的向量

### Requirement: OpenAI-Compatible Providers

系统 SHALL 提供 OpenAI-compatible LLM provider 和 embedding provider。

OpenAI-compatible provider MUST 使用配置中的 base URL、API key 和 model。缺少必要配置时，系统 MUST 报告 provider 未就绪，而不是泄露密钥或导致服务启动失败。

#### Scenario: Missing OpenAI API key

- **WHEN** provider 配置为 `openai` 但 API key 为空
- **THEN** provider 状态为未就绪，并说明缺少 API key

#### Scenario: Create OpenAI-compatible clients

- **WHEN** provider 配置为 `openai` 且必要配置完整
- **THEN** 系统可以创建 LLM 与 embedding provider 实例
