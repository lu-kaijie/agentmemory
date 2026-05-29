## MODIFIED Requirements

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
