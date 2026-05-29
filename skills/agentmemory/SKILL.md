---
name: agentmemory
description: AgentMemory 长期记忆使用协议。Use when coding agents need to query historical context, user preferences, prior decisions, save explicit long-term memory, record stage summaries, or maintain AgentMemory search indexes through CLI or REST API.
---

# AgentMemory

优先使用 `agentmemory` CLI；CLI 不可用时再调用本地 REST API。查询类命令优先加 `--json`，便于解析。

## 先查询

在这些场景先查记忆：

- 新任务涉及已有项目、长期偏好或历史决策。
- 用户提到“之前”、“上次”、“记得”、“按以前方式”。
- 准备修改关键模块，但不确定过去约定。

默认先用：

```bash
agentmemory search "<query>" --mode hybrid --limit 5 --json
```

需要基于证据解释结果时再用：

```bash
agentmemory smart-search "<question>" --mode hybrid --limit 5 --json
```

模式选择：

- `keyword`：文件名、函数名、错误码、命令、精确术语。
- `vector`：自然语言、同义表达、语义相近问题。
- `hybrid`：默认选择，合并关键词和语义结果。

REST 兜底：

- `POST /agentmemory/search`
- `POST /agentmemory/smart-search`

## 写入记忆

`observe` 用于阶段性工作过程，不用于每一步操作。适合：

- 完成一次探索并形成结论。
- 完成一组修改并验证结果。
- 发现关键问题、风险或用户纠正方向。
- 任务结束时总结本轮工作。

```bash
agentmemory observe \
  --content "<阶段性总结>" \
  --project "<project>" \
  --files "<file1>,<file2>" \
  --concepts "<concept1>,<concept2>" \
  --language zh \
  --json
```

`remember` 用于用户明确要求长期保留的事实、偏好、决策或经验：

```bash
agentmemory remember \
  --content "<需要长期保留的内容>" \
  --type decision \
  --concepts "<concept1>,<concept2>" \
  --language zh \
  --json
```

REST 兜底：

- `POST /agentmemory/observe`
- `POST /agentmemory/remember`

## 低频规则

不要在每次文件读取、每次编辑、每次命令执行或每次测试后调用 `observe`。把同一阶段的信息合并成一条记录。

当前会话内的信息通常已经在 agent 上下文中；AgentMemory 主要服务于跨会话、跨任务的长期复用。

## 索引维护

如果搜索结果明显缺失，先检查索引：

```bash
agentmemory index status --json
```

有 pending、failed 或缺失索引时：

```bash
agentmemory index repair --json
```

只有在索引严重不一致时才重建：

```bash
agentmemory index rebuild --json
```

## 不要保存

- API key、token、密码、私密凭据。
- 大段原始日志或无关命令输出。
- 未验证猜测、临时想法、明显过期的信息。
- 没有证据来源的 LLM 编造结论。

当前版本不要使用未实现的自动采集、上下文注入、知识库页面、导出或删除操作。
