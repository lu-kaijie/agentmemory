## Why

当前 memory search、LLM Wiki 和 context 注入已经可用，但仍偏 P0：检索以召回优先，重复 Wiki knowledge 容易累积，直接注入给 shell-based agent 的记忆边界还需要更系统地表达。下一步需要把这三点一起收敛，否则 context 和 Wiki 会把低相关或重复 evidence 放大到 agent prompt 中。

## What Changes

- 为 search 增加相关性门控：支持最小分数阈值、短查询/泛词查询处理、keyword phrase/AND 策略、hybrid rerank 和 smart-search evidence 二次过滤。
- 优化 LLM Wiki 知识层：对 distilled knowledge 做 fingerprint 去重、相似合并、lesson 强化/衰减字段、crystal 稳定生成边界，并让 rebuild 优先复用已有 knowledge。
- 强化 context 注入身份：提供统一的 AgentMemory context envelope，明确这是外部长期记忆证据，不是系统指令或用户新指令；同时保留 JSON 结构化路径。
- 更新 Skill 和项目文档，说明 agent 如何使用相关性分数、source ids、confidence 和身份边界。
- 不引入破坏性 API；默认行为应更少噪声，必要时通过参数保持宽召回。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `memory-search`: 增加相关性阈值、泛词处理、hybrid rerank 和 smart-search evidence 过滤要求。
- `memory-wiki`: 增加 distilled knowledge 去重/合并、lesson 强化、crystal 稳定边界和 rebuild 复用要求。
- `memory-context`: 增加统一 AgentMemory context envelope 和注入身份/边界要求。
- `agent-skill`: 更新 agent 使用协议，要求直接注入时识别 AgentMemory 来源并结合 evidence/confidence 判断。

## Impact

- Affected code:
  - `src/agentmemory/core/search.py`
  - `src/agentmemory/core/service.py`
  - `src/agentmemory/core/models.py`
  - `src/agentmemory/cli.py`
  - `skills/agentmemory/SKILL.md`
  - `PROJECT.md`
- Affected specs:
  - `openspec/specs/memory-search/spec.md`
  - `openspec/specs/memory-wiki/spec.md`
  - `openspec/specs/memory-context/spec.md`
  - `openspec/specs/agent-skill/spec.md`
- Tests will cover reduced noisy recall, deduped Wiki knowledge, stable crystal boundaries, and prompt output identity.
