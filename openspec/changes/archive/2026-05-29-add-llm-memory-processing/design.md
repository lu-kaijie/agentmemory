## Context

系统目前已经能保存 observation、memory、session 和 audit，也已经具备必需的真实 OpenAI-compatible LLM/embedding provider。但 `observe` 仍然只保存原始工作过程，尚未把 agent 工作过程转换成 summary、候选长期记忆或后续 Wiki 更新所需的结构化证据。

本变更负责把 LLM 放入 observation 写入链路。它不实现搜索或 Wiki 页面维护，而是生成后续 RAG 和 Wiki 需要的派生数据。

## Goals / Non-Goals

**Goals:**

- 在 `observe` 保存 observation 后调用 LLM provider。
- 为每条 observation 创建 LLM processing job。
- 保存 observation summary。
- 保存 candidate memories，但不自动接受为长期 memory。
- 记录 LLM processing 成功、失败、错误信息和来源 observation id。
- 提供 REST 和 CLI 查询 summaries、candidate memories 和 processing jobs。
- 为 LLM processing 成功/失败写 audit。

**Non-Goals:**

- 不实现 RAG 索引、FTS5、LanceDB 或搜索。
- 不实现 Wiki 页面更新或 Wiki update job 真正执行。
- 不把 candidate memory 自动保存为 memory。
- 不实现后台队列、定时任务、重试调度或并发 worker。
- 不实现 embedding 写入。

## Decisions

### 1. Observe 后同步处理

`observe` 完成原始 observation 保存后同步调用 LLM。这个决策只适用于当前 Skill + CLI/API 的低频入口，不适用于未来 hook 高频采集入口。

1. 创建 `llmProcessingJob`，状态为 `running`。
2. 调用 `llm.summarize` 生成 summary。
3. 调用 `llm.extract_memories` 生成 candidate memories。
4. 保存 summary、candidate memories。
5. 将 job 状态更新为 `done`。
6. 写入 audit。

同步处理可以保证第一版写入后立即有 LLM 结果，便于验收和后续功能复用。后续后台任务 change 可以把同一套 service 方法迁移到异步 worker。

### 1.1 触发频率约束

因为每次 `observe` 都会触发真实 LLM 调用，Skill 必须把 `observe` 定义为阶段性动作，而不是每步动作：

- 完成一次有价值的探索后调用。
- 完成一个重要修改并验证后调用。
- 发现关键问题或关键结论后调用。
- 用户纠正方向或明确要求记录阶段总结后调用。
- 不在每次文件读取、每次编辑、每次命令执行、每次测试后调用。

当前 change 不实现 hook。未来如果加入 hook，高频 PostToolUse 事件不得默认同步调用本流程，应通过异步 job、批处理、节流或显式开关处理。

### 2. LLM 失败不丢 observation

Observation 是原始证据，必须先保存。LLM 失败时：

- observation 保留；
- job 状态更新为 `failed`；
- job 保存 `lastError`；
- audit 写入 `llm_processing_failed`；
- API/CLI 返回 observation 结果和 processing 状态。

这样可以保证原始数据不丢，同时符合“AI 必须参与”：系统会尝试真实 LLM 调用，并显式记录失败。

### 3. Candidate memory 不自动入库

Candidate memory 是 LLM 建议，不等同于用户显式长期 memory。本变更保存到 `memoryCandidates`，字段包含：

- `id`
- `observationId`
- `content`
- `type`
- `confidence`
- `concepts`
- `files`
- `language`
- `status`: `candidate`
- `createdAt`

后续 governance 或 review change 再决定如何接受、拒绝、合并或转成正式 memory。

### 4. Summary 作为独立派生数据

Summary 保存到 `summaries`，字段包含：

- `id`
- `observationId`
- `content`
- `source`
- `language`
- `createdAt`

后续 RAG change 可以直接对 summaries 建 FTS5 和 embedding 索引。

### 5. Provider 注入

`MemoryCoreService` 当前只依赖 `StateKV`。本变更扩展为可选注入 provider bundle 或 LLM provider：

- API app 使用已创建的 provider bundle。
- CLI 本地路径也创建 provider bundle。
- 单元测试可以使用真实 provider 或一个测试专用 stub。stub 只用于测试 service 行为，不作为运行 provider，也不出现在产品配置中。

## Risks / Trade-offs

- 同步 LLM 会增加 observe 延迟 -> 第一版优先保证 AI 结果立即可验收，后续后台任务优化。
- Skill 写得过于激进会拖慢 agent -> 在 Skill 规则中限制 `observe` 只能低频、阶段性触发。
- 未来 hook 可能产生高频 observation -> hook 不得默认同步触发 LLM，必须引入节流/队列/显式开关。
- LLM 普通 JSON prompt 输出不稳定 -> candidate memory extraction 使用 XML-like `<memory>` 标签格式并只解析标签内容；JSON 或普通文本输出不得被兜底保存为 candidate。
- Candidate memory 可能有误 -> 不自动保存为正式 memory，保留人工/后续治理入口。
- 测试真实 LLM 有网络和成本 -> 只对 provider 层保留真实调用测试；service 行为测试使用受控 stub，避免每个单元测试都调用远程模型。

## Migration Plan

无历史迁移。已有 observation 不自动补处理；后续可通过 repair/rebuild change 对历史数据补跑。

实施顺序：

1. 扩展 KV scopes 和 Pydantic 模型。
2. 新增 LLM memory processing service/helper。
3. 扩展 `observe` 返回 processing 结果。
4. 增加 REST/CLI 查询入口。
5. 添加单元、REST、CLI 和真实 provider smoke 测试。
