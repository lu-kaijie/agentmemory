## Context

当前系统已经具备 observation/memory 写入、LLM 摘要和候选记忆、混合检索、治理导出删除、Skill 和 Viewer。缺口是 LLM Wiki 思想下的长期知识沉淀：系统还不能把多次任务中的 evidence 持续提炼成稳定、可读、可引用、可演化的知识层。

本变更中的 Wiki 页面是 P0 入口层，不是 LLM Wiki 的最终完整形态。长期方向是把原始 evidence 先沉淀为 semantic facts、procedural patterns、lessons、crystals 和 reflect insights，再由 Wiki 页面聚合展示这些 distilled knowledge。当前变更直接实现 semantic/procedural/lesson/crystal 四类 distilled knowledge，并保留 reflect insights、graph 等更重能力给后续 change。

## Goals / Non-Goals

**Goals:**

- 建立 Wiki 页面和 Wiki update job 两个状态域。
- 建立 distilled knowledge 状态域，覆盖 semantic、procedural、lesson 和 crystal 四类知识。
- observation、memory、summary 进入系统后创建 Wiki update job。
- 提供后台 worker 和手动入口处理 pending Wiki jobs。
- 使用真实 LLM 根据 evidence 生成 distilled knowledge。
- 使用真实 LLM 根据 evidence、distilled knowledge 和现有页面生成 Wiki update proposal。
- 应用 proposal 创建或更新 Wiki 页面，并保留 `sourceIds`。
- distilled knowledge 和 Wiki 页面写入 audit，并进入 FTS5/LanceDB 搜索索引。
- 通过 REST、CLI 和 Viewer 只读查看 distilled knowledge、Wiki 页面与 jobs。
- 明确 Wiki 页面是长期知识沉淀系统的 P0 聚合视图，后续可扩展为 semantic/procedural/lessons/crystals/reflect 驱动的知识层。

**Non-Goals:**

- 不实现 Hook、MCP 或自动外部采集。
- 不实现 Wiki 手动编辑 UI。
- 不实现复杂冲突合并、多人协作锁或权限系统。
- 不实现知识图谱节点/边抽取。
- 不实现 reflect insights。
- 不实现 import/export 版本迁移之外的 Wiki 导入逻辑。
- 不让每次 observe 同步等待 Wiki LLM 处理完成。

## Decisions

### 1. Wiki 更新异步化，写入只入队

`observe`、`remember` 和 summary 保存后只创建 `wiki_update_job`，不在写入路径同步调用 Wiki LLM。`agentmemory serve` 启动后台 worker 处理 pending jobs；CLI/REST 也提供 `wiki update` 和 `wiki rebuild` 手动补偿。

替代方案是在每次写入后同步更新 Wiki，但这会显著拖慢 agent 工作流，也违背低频关键节点触发策略。

### 2. 第一版使用固定 topic 集合

第一版 topic 固定为：

- `personal_preferences`
- `project_overview`
- `technical_decisions`
- `troubleshooting`
- `files_and_modules`
- `workflow_habits`

LLM 可以在这些 topic 中选择目标页面。这样能减少页面碎片和 prompt 不稳定性，也便于 Viewer 和 agent 读取。

替代方案是完全开放 topic，但第一版容易生成大量近似页面。

这些固定 topic 不是最终知识模型，只是 P0 的可读聚合入口。后续实现 semantic facts、procedural patterns、lessons、crystals 和 reflect insights 后，Wiki 页面应逐步变成这些 distilled records 的聚合视图，而不是每次直接从单条 evidence 改写页面。

### 3. 先提炼 distilled knowledge，再更新 Wiki 页面

处理 Wiki job 时先调用 LLM 从 evidence 中提炼四类记录：

- `semantic`：稳定事实和项目知识。
- `procedural`：流程、习惯和做事模式。
- `lesson`：经验教训。
- `crystal`：一次 change 或一段工作的高层摘要。

这些记录保留 `sourceIds`、`concepts`、`files` 和 `confidence`，会写入 audit 和搜索索引。随后 Wiki update 使用原始 evidence、distilled knowledge 和现有页面共同生成页面更新。这样第一版不只是 6 个页面，而是具备 Raw -> Distilled -> Wiki 的最小闭环。

### 4. Proposal 结构使用 XML-like 输出

Wiki LLM 输出采用 XML-like 标签解析，避免依赖模型稳定输出 JSON。建议结构：

```text
<wiki_update topic="technical_decisions" title="技术决策" confidence="0.8">
<content>...</content>
</wiki_update>
```

系统只在解析到有效 `wiki_update` 时应用更新。无效输出标记 job failed，并保留 observation/memory/summary 原始数据。

Knowledge distillation 也使用 XML-like 输出：

```text
<knowledge>
<item kind="semantic" confidence="0.8">
<content>稳定事实。</content>
<concepts>search,wiki</concepts>
<files>src/agentmemory/core/service.py</files>
</item>
</knowledge>
```

无有效 item 时可以返回 `<knowledge/>`。

### 5. Wiki 页面按 topic upsert

每个 topic 第一版最多一个页面。应用 update 时，如果页面存在则更新 content、sourceIds、confidence 和 updatedAt；如果不存在则创建新页面。`sourceIds` 追加去重，保留 evidence 可追溯。

### 6. Distilled knowledge 和 Wiki 页面进入搜索索引

Distilled knowledge 和 Wiki 页面是长期知识层，必须作为 search source type 参与 keyword/vector/hybrid search。索引失败不回滚 knowledge 或 Wiki 页面更新，但必须记录 failed index job，后续 repair/rebuild 可补齐。

### 7. Viewer 只读展示 Wiki

Viewer 增加 Wiki 页面、distilled knowledge 和 Wiki jobs tab，只通过 REST 读取数据。不在本变更提供编辑、删除、应用候选或强制 rebuild UI，避免破坏性操作进入第一版 Viewer。

### 8. 后续知识沉淀路线

LLM Wiki 的完整路线应按层推进：

- Raw layer：observation、memory、summary 和 searchable evidence。
- Distilled layer：semantic facts、procedural patterns、lessons 和 crystals。本变更已实现最小版本。
- Synthesis layer：Wiki pages、reflect insights，后续可接入 graph。
- Retrieval layer：search、smart-search、context、Skill 和 Viewer。

本变更完成 Raw -> Distilled -> Wiki page 的最小闭环。下一阶段应优先补 reflect insights、知识冲突处理、reinforce/decay 和 graph。

## Risks / Trade-offs

- [Risk] LLM Wiki update 内容不稳定或过度改写。  
  Mitigation：固定 topic，先生成 distilled records，再聚合 Wiki 页面，要求保留 sourceIds，解析失败不应用。

- [Risk] Wiki worker 增加模型调用成本。  
  Mitigation：写入只入队，后台低频处理；支持手动 update/rebuild；同 topic pending job 可合并。

- [Risk] 页面内容越来越长。  
  Mitigation：第一版保留内容更新，后续增加压缩策略、页面长度上限，并把稳定知识拆入 semantic/procedural/lessons/crystals。

- [Risk] Wiki search 召回噪声。  
  Mitigation：保留 sourceType 过滤能力，后续结合检索相关性优化做阈值和二次过滤。

- [Risk] Distilled knowledge 重复增长。  
  当前每个 Wiki job 都会对关联 evidence 执行 distillation。多次 `wiki update` 或 `wiki rebuild --all` 处理同一批 `sourceIds` 时，可能生成内容相近的 semantic/procedural/lesson/crystal records。  
  Mitigation：后续增加 `kind + normalized content` 或 `kind + sourceIds + content fingerprint` 去重；对近似内容用 embedding similarity 或 LLM merge；为 lesson 增加 reinforce/decay；为 crystal 增加按 session/change/source group 的稳定边界；Wiki rebuild 优先复用已有 distilled knowledge。

## Migration Plan

- 新增 `KV.wikiPages` 和 `KV.wikiUpdateJobs` scope，无需迁移既有数据。
- 旧数据不会自动生成 Wiki 页面，用户可运行 `agentmemory wiki rebuild --all` 从现有 observations、memories 和 summaries 创建 Wiki jobs 并处理。
- 回滚时可保留 Wiki scope 数据，不影响 observation/memory/search/governance 主流程。
