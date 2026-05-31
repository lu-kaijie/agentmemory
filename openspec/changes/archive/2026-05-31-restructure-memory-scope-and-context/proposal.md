## Why

AgentMemory 已经具备记忆写入、RAG、LLM Wiki 和 context 输出，但核心模型仍以通用 search source types 为中心。Agent 接入时更需要一个稳定的用户心智模型：全局记忆、项目记忆，以及面向 agent 的固定格式上下文。

本 change 将把记忆获取方式从“搜索结果打包”推进到“按 Global / Project 分层组织，并由 LLM 生成高信号 synthesis 的 agent-native context”。Session 只作为内部 evidence 容器和历史追溯来源，不作为用户必须管理的主模型。

## What Changes

- 引入 Global / Project 两层主记忆组织：
  - Global：跨项目用户偏好、固定规则、通用 lesson、跨项目 insight。
  - Project：项目画像、项目固定记忆、项目 Wiki synthesis、项目 knowledge、项目 lessons/crystals/insights。
- Session：保留为内部 evidence 容器，用于 observations、summaries、recent evidence 和历史追溯，但不要求用户显式 start/end。
- 增加 Project Profile 能力，长期维护项目目标、技术栈、关键文件、常用命令、约定和常见问题。
- 增加 Pinned Memory / Slots 能力，把高优先级记忆显式固定到 context。
- 重构 agent context 输出为固定 envelope 和固定 sections，而不是简单搜索结果拼接。
- Context 输出优先使用 LLM 整合后的 synthesis；普通 list/search/debug 输出继续返回结构化原始结果，不强制 LLM 重写。
- Search 保持通用证据检索能力，但 context 默认按 Global → Project → Recent Sessions → Evidence 的顺序组织。
- LLM Wiki consolidation、reflect 和 project profile 更新需要按 scope 工作，避免全局记忆和项目记忆混杂。

## Capabilities

### New Capabilities

- `memory-scope`: 定义 Global / Project 主记忆层级、scope 字段、project 一等实体，以及 session 作为内部 evidence 容器的行为。
- `project-profile`: 维护面向 agent 的项目画像，并作为 context 的高优先级来源。
- `pinned-memory`: 支持全局和项目级 pinned memory/slots，稳定注入 agent context。
- `agent-context-format`: 定义固定格式、LLM synthesis 优先的 agent context envelope。

### Modified Capabilities

- `memory-core`: session、memory、observation、summary 需要明确挂接 scope/project。
- `memory-context`: context retrieval defaults、packing 和 prompt output 改为分层格式。
- `memory-search`: search 支持 scope/project/session 过滤，并保持 evidence 查询职责。
- `memory-wiki`: consolidation 和 Wiki records 支持 global/project scope。
- `memory-core-interfaces`: CLI/REST 增加 project/profile/pinned/context 相关接口。
- `agent-skill`: Skill 指导 agent 使用新的分层 context 和 pinned/profile 能力。

## Impact

- Core models：新增 project、scope、pinned/profile/context section 相关模型。
- StateKV：新增 projects、pinned memory/profile 相关 scopes。
- Service：context、search、wiki consolidation、session lifecycle、maintenance 需要按 scope/project 处理。
- CLI/REST：新增 project profile、pinned memory 管理和分层 context 输出。
- Tests：覆盖 Global / Project 分层、内部 session evidence、fixed context format、LLM synthesis、scope filtering 和兼容导入导出。
- Docs/Skill：更新为新的主架构，避免继续把 context 描述为普通 search result packing。
