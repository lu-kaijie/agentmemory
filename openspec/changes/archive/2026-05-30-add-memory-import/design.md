## Context

当前 `export_data` 已能导出治理数据，并记录 export audit。缺口是导出的 JSON 不能被 CLI/REST 恢复到新数据库，也没有明确的 schema 兼容校验。这个能力需要跨 core service、状态写入、索引补建、CLI/REST 和测试。

## Goals / Non-Goals

**Goals:**

- 支持导入当前 export JSON，并恢复所有可治理集合。
- 明确兼容版本字段，第一版支持当前 `version` 和 `schemaVersion=1`。
- 导入时校验结构，按 id 保守去重，返回 imported/skipped/errors 摘要。
- 导入后补建搜索索引，让恢复的数据能被 search/context 使用。
- 为 import 写入 audit，便于治理追踪。

**Non-Goals:**

- 不实现跨版本复杂迁移框架，只做基础版本兼容校验。
- 不导入或恢复 provider secrets、环境变量或运行时配置。
- 不覆盖已有同 id 数据；冲突时跳过并在结果中报告。
- 不导入外部任意格式，只接受 AgentMemory export JSON。

## Decisions

- **使用 `schemaVersion` 作为导入兼容字段。** `version` 继续表示应用版本，`schemaVersion=1` 表示治理 payload schema。为兼容当前导出，缺失 `schemaVersion` 但 `version` 存在时按 schema 1 处理。
- **保守去重，不覆盖已有 id。** 每个 KV scope 按 record id 检查，已存在则 skipped，避免破坏当前库。
- **先写状态，再 repair 索引。** 导入主要恢复 KV 数据；写入完成后调用 search repair 或逐条 index document，保证可搜索。
- **audit 不照搬为当前行为。** 导入 payload 内的历史 audit 可以作为历史记录恢复；本次导入额外写一条新的 `import` audit，记录本次操作摘要。
- **REST 直接接收 JSON payload，CLI 从文件读取。** CLI 负责文件 IO，REST 负责服务调用，core service 接收已解析 payload。

## Risks / Trade-offs

- **导入历史 audit 与当前 audit 混合** → 本次 import audit 记录 source 和 timestamp，可区分恢复数据与当前操作。
- **旧 payload 字段缺失** → Pydantic 默认值和基础兼容校验允许缺失可选字段，关键字段缺失则记录错误并跳过该记录。
- **大量导入后索引修复耗时** → 第一版同步修复，后续可改后台任务。
- **同 id 但内容不同** → 第一版跳过已有 id，不做覆盖或合并，结果中报告 skipped。
