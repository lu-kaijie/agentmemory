## 1. 产品与项目基线

- [ ] 1.1 创建 AI native 产品文档，说明个人长期记忆、Skill + CLI + API 接入、RAG + LLM Wiki 双层知识库、P0/P1/P2 范围和验收标准
- [ ] 1.2 初始化 Python/FastAPI 项目结构、包管理、lint、format 和测试框架
- [ ] 1.3 定义环境变量读取、默认值、配置校验和敏感值隐藏规则
- [ ] 1.4 添加本地开发脚本、测试脚本和示例 `.env`

## 2. LLM Provider

- [ ] 2.1 定义 OpenAI-compatible `LLMProvider` 接口，覆盖摘要、记忆提炼、搜索解释、上下文压缩和 Wiki 更新
- [ ] 2.2 实现 fake LLM provider，用于单元测试和离线开发
- [ ] 2.3 实现 OpenAI-compatible LLM provider，并通过 base URL、model 和 API key 配置
- [ ] 2.4 定义并实现 OpenAI-compatible `EmbeddingProvider`
- [ ] 2.5 在健康检查中报告 LLM 和 embedding provider 可用性、模型名和最近错误

## 3. 状态层

- [ ] 3.1 实现 `StateKV` 抽象和文件型 SQLite 持久化
- [ ] 3.2 定义 `KV.sessions`、`KV.observations`、`KV.memories`、`KV.summaries`、`KV.wikiPages`、`KV.indexJobs`、`KV.wikiUpdateJobs`、`KV.relations`、`KV.graphNodes`、`KV.graphEdges` 和 `KV.audit`
- [ ] 3.3 实现 `generateId`、`fingerprintId`、时间戳生成和基础去重
- [ ] 3.4 实现 audit 写入工具，覆盖保存、删除、导入和导出

## 4. 核心记忆能力

- [ ] 4.1 实现 `mem::observe`，保存 observation 并维护 session 统计
- [ ] 4.2 实现 observation 后的 LLM 摘要、候选记忆提炼和 Wiki 更新任务
- [ ] 4.3 实现 `mem::remember`，保存用户显式 memory 并写入 audit
- [ ] 4.4 实现 session start/end 和 session summary 更新
- [ ] 4.5 实现 LLM 或 embedding 失败时的 pending/failed 状态和重试入口
- [ ] 4.6 实现 `mem::wiki-update` 和 Wiki 页面来源引用维护
- [ ] 4.7 实现 `wiki_update_job` 入队、合并、处理、失败记录和重试

## 5. 搜索与上下文

- [ ] 5.1 实现关键词或 BM25 索引，支持 query、limit、sessionId 和 project 过滤
- [ ] 5.2 集成 LanceDB 向量索引，支持 memory、summary、Wiki 页面和重要 observation 的 embedding 写入与检索
- [ ] 5.3 实现 `mem::search`，返回 observation、memory、summary 和 Wiki 页面的结构化结果
- [ ] 5.4 实现 `mem::smart-search`，组合关键词召回、embedding 召回和 LLM 匹配说明
- [ ] 5.5 实现 `mem::context`，按 token budget 返回可注入上下文
- [ ] 5.6 实现 LLM 上下文压缩，并保留来源 id 引用
- [ ] 5.7 实现 `index_job` 入队、embedding 异步更新、索引 repair 和 rebuild

## 6. CLI、Skill 与 REST API

- [ ] 6.1 实现 REST 服务和统一响应格式 `{ status_code, body, headers? }`
- [ ] 6.2 实现 bearer token 认证和公开健康检查例外
- [ ] 6.3 实现 `/agentmemory/observe`、`/agentmemory/remember`、`/agentmemory/search`、`/agentmemory/smart-search`、`/agentmemory/context` 和 `/agentmemory/wiki`
- [ ] 6.4 实现 `/agentmemory/export`、`/agentmemory/health` 和治理删除端点
- [ ] 6.5 实现 CLI 命令：`serve`、`observe`、`remember`、`recall`、`context`、`wiki`、`index`、`export` 和 `doctor`
- [ ] 6.6 创建 `skills/agentmemory/SKILL.md`，说明 recall、context、remember、observe、wiki 的触发场景，CLI 优先和 REST 兜底方式
- [ ] 6.7 为 REST adapter 和 CLI 添加字段白名单、结构化错误和 JSON 输出测试

## 7. Web Viewer

- [ ] 7.1 实现 Web Viewer 的 memories、sessions、search、Wiki、health 页面
- [ ] 7.2 实现简单关系图 API 和 Viewer 图谱展示
- [ ] 7.3 实现 Viewer 与 REST API 的统一认证和错误展示

## 8. 治理、Viewer 与后台任务

- [ ] 8.1 实现 export/import JSON 版本字段和基础兼容校验
- [ ] 8.2 实现治理删除和 audit 查询
- [ ] 8.3 实现 Wiki 更新审计和页面来源追踪
- [ ] 8.4 实现后台任务调度，处理 index repair、embedding 更新、Wiki update、failed retry 和页面压缩
- [ ] 8.5 为高级能力开关添加配置测试，确认关闭时核心功能可用

## 9. 测试与验收

- [ ] 9.1 添加状态层、核心函数、LLM provider fake、embedding provider fake、搜索和审计单元测试
- [ ] 9.2 添加 REST API 集成测试，覆盖认证、保存、搜索、Wiki、导出和健康检查
- [ ] 9.3 添加 CLI 测试，覆盖 remember、recall、context、wiki 和 JSON 输出
- [ ] 9.4 添加 Viewer 集成测试，覆盖搜索、Wiki、health 和关系图数据加载
- [ ] 9.5 完成 P0 端到端验收：Skill 指导 agent 调用 CLI/API 写入 observation，LLM 生成摘要和 Wiki 更新，CLI/REST 能搜到，memory 能保存、导出、删除并产生审计
