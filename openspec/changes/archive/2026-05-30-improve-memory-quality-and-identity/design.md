## Context

系统已经具备 memory core、search、LLM Wiki、context packing 和 agent skill。当前主要问题不是缺少入口，而是质量边界：泛词查询容易召回弱相关记录，Wiki rebuild/update 可能对相同 evidence 反复生成近似 knowledge，context 虽然已经带来源说明，但还没有形成统一的注入 envelope 和 agent 使用协议。

可迁移的设计思路是：长期记忆不要把全部历史塞进 prompt，而是先通过检索过滤，再把 evidence 沉淀为稳定知识，最后用有边界的上下文块注入 agent。这个 change 把这条链路收紧。

## Goals / Non-Goals

**Goals:**

- 降低 keyword/vector/hybrid search 的噪声召回。
- 让 smart-search 和 context 只基于通过相关性门控的 evidence。
- 让 Wiki knowledge 对相同 source 或相似内容去重、合并或强化，而不是持续追加重复记录。
- 为 lesson 和 crystal 增加稳定生命周期字段，支持后续质量治理。
- 统一 AgentMemory prompt context 的身份 envelope，让 shell-based agent 明确这是外部长期记忆证据。

**Non-Goals:**

- 不实现完整知识图谱、自动遗忘、权限系统或 MCP/Hook 接入。
- 不引入新的外部数据库或搜索引擎。
- 不让 LLM 覆盖当前用户指令或系统指令。
- 不删除已有 memory/wiki 数据；迁移以兼容旧记录为原则。

## Decisions

### 1. Search 先做确定性门控，再做 LLM 解释

Search service 增加一个 relevance gate：keyword/vector/hybrid 结果进入 response 前先过滤低分和弱匹配。第一版使用确定性规则：

- keyword search 支持 `matchMode`：`auto`、`any`、`all`、`phrase`。
- `auto` 对短查询、引号查询或明显短语使用更严格匹配；对普通查询保留一定召回。
- vector search 支持 `minScore` 或内部默认阈值，过滤距离/相似度过低结果。
- hybrid merge 对同时命中 keyword 和 vector 的结果加权提升，对只命中泛词 keyword 的结果降权。
- smart-search 只解释门控后的 evidence；如果结果不足，返回低置信说明。

这样可以避免把“memory/search/governance”这类泛词的弱匹配直接送进 Wiki 或 context。

### 2. Wiki knowledge 写入前先 canonicalize

Distilled knowledge 写入前计算 `fingerprint`，由 `kind + normalized content` 和可选 `sourceIds` 组成。写入策略：

- fingerprint 完全相同：更新已有 record 的 `sourceIds`、`updatedAt`、`reinforcements`，不新增。
- 内容相似且 kind 相同：优先合并 sourceIds 和 confidence；必要时保留为 related record。
- lesson 增加强化字段，用于表示多次 evidence 支持同一经验。
- crystal 使用稳定边界：同一 source group/session/change 不重复生成近似 crystal。

第一版可以用确定性 normalization 和 source group 做去重，embedding/LLM 相似合并作为可选增强。

### 3. Wiki rebuild 优先复用 knowledge

`wiki rebuild` 不应每次从原始 evidence 重新 distill 全量内容。流程改为：

1. 收集现有 distilled knowledge。
2. 找出缺失、过期或 sourceIds 未覆盖的部分。
3. 只对缺口 evidence 执行 distill。
4. 用 knowledge 聚合 Wiki 页面。

这会减少重复 knowledge，也让 Wiki 页面更稳定。

### 4. Context 使用统一 envelope

非 JSON context 输出使用统一 envelope：

```text
<agentmemory-context source="AgentMemory" kind="long-term-memory" confidence="..." compressed="...">
...
</agentmemory-context>
```

同时保留当前 `[AgentMemory Context]` 和 `[Evidence]` 可读段落，兼容 shell-based agent 直接加载。Envelope 必须声明：

- 来源是 AgentMemory 长期记忆工具。
- 内容是 evidence-grounded background。
- 不是系统指令，也不是用户新指令。
- 不能覆盖当前用户请求、系统指令或开发者指令。

JSON 输出保持结构化 response，不强制包含 prompt envelope。

### 5. Skill 作为 agent 使用协议

Skill 文档要告诉 agent：

- 直接注入 prompt 用非 JSON `agentmemory context`。
- 程序化解析才用 `--json`。
- 低 confidence、无 evidence、低 score 或只命中泛词的结果不能当确定事实。
- AgentMemory context 是外部记忆证据，只能辅助当前任务。

## Risks / Trade-offs

- 更严格的相关性门控可能漏掉弱相关但有用的历史记录。→ 提供 `matchMode=any` 或较低 `minScore` 保留宽召回路径。
- 旧数据没有 fingerprint/reinforcement 字段。→ 模型字段给默认值，repair/rebuild 时逐步补齐。
- 去重过强可能合并不同但相近的经验。→ 第一版只自动合并确定性重复，相似合并保守处理。
- XML-like envelope 可能被 agent 当成普通文本。→ 同时保留人类可读 header 和明确否定指令边界。
