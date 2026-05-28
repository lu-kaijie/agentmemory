## Why

系统已经具备真实 LLM/embedding provider，但 observation 写入后仍只是保存原始文本。为了满足 AI native 产品定位，第一版需要让 LLM 从记忆写入链路开始参与，把 agent 工作过程转化为 summary 和候选长期记忆。

本变更让 `observe` 在保存 observation 后调用 LLM 进行记忆处理，并保存处理结果和状态，为后续搜索、RAG 索引和 LLM Wiki 更新提供结构化数据源。

## What Changes

- 新增 LLM memory processing 能力：
  - 对 observation 生成 summary。
  - 从 observation 中提炼 candidate memories。
  - 保存 processing 状态、错误、来源 observation id 和时间戳。
- 修改 `observe` 写入流程：
  - observation 保存成功后必须触发 LLM processing。
  - LLM processing 成功后保存 summary 和 candidate memories。
  - LLM processing 失败时 observation 保留，但 processing 状态必须记录为 failed，并写入 audit。
- 明确性能边界：
  - Skill 只能在阶段性节点调用 `observe`。
  - 不允许要求 agent 在每次工具调用、每次文件读取或每次编辑后调用 `observe`。
  - 未来 hook 如需采集高频事件，不能默认同步调用 LLM，必须走队列、节流或显式开关。
- 扩展 KV scope：
  - `summaries`
  - `memoryCandidates`
  - `llmProcessingJobs`
- 扩展 REST/CLI 查看能力：
  - `GET /agentmemory/summaries`
  - `GET /agentmemory/memory-candidates`
  - `GET /agentmemory/llm-processing-jobs`
  - `agentmemory summaries`
  - `agentmemory memory-candidates`
  - `agentmemory llm-processing-jobs`
- 不实现 RAG 索引、FTS5、LanceDB、搜索、自动接受候选 memory 或 Wiki 页面更新。

## Capabilities

### New Capabilities

- `llm-memory-processing`: observation 写入后的 LLM summary、candidate memory 提炼、处理状态和审计能力。

### Modified Capabilities

- `memory-core`: `observe` 成功保存 observation 后触发 LLM memory processing，并新增 summary/candidate/job 列表能力。
- `memory-core-interfaces`: REST 和 CLI 增加 summary、candidate memory 和 LLM processing job 查询入口。

## Impact

- 修改 memory core service，注入 LLM provider 或 provider bundle。
- 新增 summary、candidate memory、LLM processing job 模型和 KV scope。
- 修改 REST app factory 和 CLI 本地函数路径。
- 增加真实 LLM 调用测试、失败路径测试和接口测试。
