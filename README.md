# AgentMemory

AgentMemory 是一个面向 coding agent 的本地长期记忆服务。它让 agent 能在跨会话、跨任务和跨工具执行时保存工作过程、复用历史决策、检索项目经验，并把可追溯的记忆上下文注入到后续任务中。

它不是普通笔记应用，也不是只做向量搜索的 RAG demo。AgentMemory 同时提供：

- 长期记忆：保存 observation、memory、session summary、Wiki 页面和审计记录。
- RAG 检索：用 SQLite FTS5 做关键词召回，用 LanceDB + embedding 做语义召回。
- LLM Wiki：用 LLM 把 RAG evidence 进一步沉淀为 semantic、procedural、lesson、crystal、insight，并维护可搜索的 topic/entity/concept/source/comparison/synthesis Wiki 页面。
- Agent 接入：提供 Skill、CLI 和 REST API，适合 Claude Code、Codex 等 shell-capable agent 使用。
- 治理能力：支持导出、导入、删除、审计、失败重试和后台维护。

## 可以做什么

AgentMemory 主要解决这些问题：

- 记录 agent 已完成的探索、修改、测试、结论和后续注意事项。
- 保存用户明确要求长期记住的偏好、事实、决策和经验。
- 在新任务开始时检索相关历史，并生成可直接放入 prompt 的上下文。
- 把分散的记忆证据整理成 Wiki 页面，减少重复搜索和重复探索。
- 导出和导入完整数据，用于迁移、备份或验收。
- 删除错误记忆，并通过 audit trail 追踪治理动作。
- 后台自动处理 embedding、Wiki update、失败重试和索引修复。

## 快速开始

### 1. 安装依赖

```bash
uv sync --extra dev
```

### 2. 配置环境变量

复制示例配置：

```bash
cp .env.example .env
```

至少填写这些项：

```bash
AGENTMEMORY_LLM_BASE_URL=https://api.openai.com/v1
AGENTMEMORY_LLM_API_KEY=...
AGENTMEMORY_LLM_MODEL=...

AGENTMEMORY_EMBEDDING_BASE_URL=https://api.openai.com/v1
AGENTMEMORY_EMBEDDING_API_KEY=...
AGENTMEMORY_EMBEDDING_MODEL=...
```

本地状态默认可放在项目内或用户目录：

```bash
AGENTMEMORY_DB_PATH=.agentmemory/agentmemory.sqlite3
AGENTMEMORY_VECTOR_DB_PATH=.agentmemory/vector
```

### 3. 启动服务

```bash
./scripts/dev.sh
```

等价于：

```bash
uv run agentmemory serve
```

默认地址：

- API: `http://127.0.0.1:3111/agentmemory/*`
- Viewer: `http://127.0.0.1:3111/agentmemory/`

Viewer 是 Vite + React 构建的只读观察面板，用于查看 Global / Project 记忆、pinned memory、project profile、context sections、Wiki/knowledge、搜索结果和关系图。

### 4. 检查配置

```bash
uv run agentmemory doctor
```

健康检查：

```bash
curl -s http://127.0.0.1:3111/agentmemory/health
```

## 记忆层级

AgentMemory 的主心智模型是 Global + Project：

- Global：跨项目偏好、通用规则、稳定习惯和跨项目经验。
- Project：当前项目的目标、技术栈、关键文件、命令、约定、Wiki synthesis 和项目经验。
- Session：内部 evidence 容器，用来归组 observations 和生成 summary；用户和 agent 不需要依赖显式 session start/end 才能正确使用记忆。

Project 默认按当前工作目录识别：`root = realpath(cwd)`，展示名默认是目录名，内部 `projectId` 是 root path 的稳定 hash。你通常只需要在项目根目录启动 agent，然后调用 `agentmemory context "<当前任务>"`。

高优先级内容可以 pin 到 context：

```bash
uv run agentmemory pin add \
  --scope project \
  --content "本项目修改前必须先跑 pytest 和 OpenSpec validate。" \
  --json
```

项目画像由 LLM 从项目 evidence 维护：

```bash
uv run agentmemory project profile --update --json
```

## 常用 CLI

显式开始一次会话是可选的，适合你想手动追踪一轮任务时使用：

```bash
uv run agentmemory session start \
  --session-id ses_demo \
  --project agentmemory \
  --cwd "$PWD" \
  --json
```

记录阶段性工作：

```bash
uv run agentmemory observe \
  --session-id ses_demo \
  --content "完成搜索模块排查，确认 FTS5 负责关键词召回，LanceDB 负责语义召回。" \
  --language zh \
  --concepts search,rag \
  --json
```

保存明确的长期记忆：

```bash
uv run agentmemory remember \
  --content "AgentMemory 的 context 输出可直接注入 agent prompt，但不能覆盖当前用户指令。" \
  --type decision \
  --scope global \
  --language zh \
  --concepts context,agent \
  --json
```

搜索记忆：

```bash
uv run agentmemory search "FTS5 LanceDB RAG" --mode hybrid --json
```

获取可注入 prompt 的上下文：

```bash
uv run agentmemory context "这个项目的 RAG 和 Wiki 怎么配合"
```

默认 context 是 project scope，会包含 global + 当前 project 的高信号记忆，并按固定 XML-like sections 输出：

- identity
- global
- project
- wiki-synthesis
- lessons-and-crystals
- recent-evidence
- evidence

生成结构化 JSON 上下文：

```bash
uv run agentmemory context "memory context Wiki knowledge" --json
```

处理 Wiki 更新：

```bash
uv run agentmemory wiki update --json
```

运行维护任务：

```bash
uv run agentmemory maintenance run --json
```

结束会话并生成 session summary：

```bash
uv run agentmemory session end \
  --session-id ses_demo \
  --content "完成 AgentMemory 基础验收。" \
  --language zh \
  --json
```

导出、导入和删除：

```bash
uv run agentmemory export --json > agentmemory-export.json
uv run agentmemory import --file agentmemory-export.json --json
uv run agentmemory forget --memory-id mem_xxx --reason "错误记忆" --json
```

## REST API

CLI 是推荐入口，REST 适合工具集成或服务化调用。

保存 observation：

```bash
curl -s http://127.0.0.1:3111/agentmemory/observe \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "ses_demo",
    "content": "完成 REST 验收。",
    "language": "zh",
    "concepts": ["rest", "acceptance"]
  }'
```

搜索：

```bash
curl -s http://127.0.0.1:3111/agentmemory/search \
  -H "Content-Type: application/json" \
  -d '{"query":"RAG Wiki", "mode":"hybrid", "limit":5}'
```

获取上下文：

```bash
curl -s http://127.0.0.1:3111/agentmemory/context \
  -H "Content-Type: application/json" \
  -d '{"query":"项目当前记忆能力", "sourceTypes":["wikiPage","knowledge","memory"]}'
```

REST 默认返回业务 JSON。需要统一响应 envelope 时，可以用 query 参数：

```bash
curl -s "http://127.0.0.1:3111/agentmemory/health?envelope=true"
```

返回形态：

```json
{
  "status_code": 200,
  "body": {},
  "headers": {}
}
```

也可以通过配置开启：

```bash
AGENTMEMORY_REST_ENVELOPE=true
```

## RAG 是怎么用的

AgentMemory 的 RAG 不是索引整个代码仓库，而是索引 agent 工作过程中产生的记忆证据：

- observation：阶段性工作记录。
- memory：用户显式保存的长期记忆。
- summary：LLM 生成的 observation summary 和 session summary。
- knowledge：从 evidence 提炼出的知识项。
- wikiPage：LLM Wiki 导航和聚合页面。
- insight：从多条知识中反思出的高层结论。

写入时，系统同步写入 SQLite FTS5，让关键词搜索立即可用；同时创建 embedding job，由后台 worker 或 `maintenance run` 写入 LanceDB 向量库。

检索时：

1. keyword search 使用 FTS5，适合精确术语、文件名、错误码、命令、函数名。
2. vector search 使用 embedding + LanceDB，适合自然语言、同义表达和跨语言召回。
3. hybrid search 合并两路结果，去重、排序，并保留 `matchSources`。
4. context 会把 Wiki、knowledge、memory 等结果打包为可注入 prompt 的上下文。

为了避免弱相关内容污染上下文，搜索还提供：

- `matchMode=auto|any|all|phrase`
- `minScore`
- `sourceTypes`
- `project`
- `language`

## LLM Wiki 是什么

RAG 更偏“找到证据”，LLM Wiki 更偏“沉淀知识”。

AgentMemory 会把 observation、memory、summary 等 evidence 先提炼为结构化知识：

- semantic：稳定事实和已确认结论。
- procedural：流程、操作方式和工作习惯。
- lesson：经验教训，支持 reinforcement。
- crystal：一组 evidence 的阶段性结晶摘要。
- insight：跨 semantic、procedural、lesson、crystal 归纳出的高层认识。

当前版本保留 6 个固定 Wiki topic 作为导航和可读聚合入口：

- 个人偏好
- 项目概览
- 技术决策
- 常见问题和修复经验
- 文件和模块说明
- 工作流习惯

这些固定 topic 不是 LLM Wiki 的本质，也不是完整知识模型。它们只是稳定入口；真正的 LLM Wiki 思想体现在 LLM 会读取多条 evidence 和已有记录，判断稳定事实、可复用流程、冲突、陈旧结论和需要合并的内容。Consolidation 可以生成动态 entity、concept、source、comparison、synthesis 页面，并用 slug 更新已有页面。

这样做的好处是：

- agent 不必每次从一堆原始 observation 里重新归纳。
- 用户可以在 Viewer 或 CLI 里直接查看稳定知识。
- context 可以优先注入更稳定的 Wiki/knowledge，再补充原始 memory。
- Wiki、knowledge 和 insight 保留 `sourceIds`，方便追溯依据。
- `wiki lint` 会让 LLM 判断 contradiction/stale，并补充 missing-source、low-confidence、orphan 等结构化检查。

处理入口：

```bash
uv run agentmemory wiki update --json
uv run agentmemory wiki consolidate --json
uv run agentmemory wiki reflect --json
uv run agentmemory wiki lint --json
uv run agentmemory wiki rebuild --all --json
uv run agentmemory wiki knowledge --json
uv run agentmemory wiki insights --json
uv run agentmemory wiki pages --json
```

## 后台维护

服务启动后可以运行统一 maintenance worker：

```bash
AGENTMEMORY_MAINTENANCE_ENABLED=true
AGENTMEMORY_MAINTENANCE_INTERVAL_SECONDS=10
AGENTMEMORY_MAINTENANCE_LIMIT=25
```

maintenance 会处理：

- pending/failed index jobs
- failed LLM processing jobs
- pending/failed Wiki update jobs
- 缺失 searchable document 的 repair
- 页面压缩的结果字段预留

手动运行：

```bash
uv run agentmemory maintenance run --json
```

## Agent 接入

项目提供 Skill：

```text
skills/agentmemory/SKILL.md
```

全局 agent 指令可以写：

```text
编码任务中使用 AgentMemory skill 管理长期记忆。
```

推荐策略：

- 新任务开始时先调用 `agentmemory context "<当前任务>"`。
- 阶段性完成探索、修改、验证或复盘后调用 `agentmemory observe`。
- 用户明确要求“记住”时调用 `agentmemory remember`。
- 不要在每次文件读取、每次命令执行后都写 observation。

## 开发与验证

运行测试：

```bash
./scripts/test.sh
```

等价于：

```bash
uv run pytest
uv run openspec validate --all --strict
```

更多设计说明见：

- [PROJECT.md](PROJECT.md)
- [docs/technical-implementation.md](docs/technical-implementation.md)
- [docs/agent-setup.md](docs/agent-setup.md)
