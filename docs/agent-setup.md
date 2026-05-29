# Agent 配置

用户可以在自己的全局 agent 指令文件中加入这一行：

```text
编码任务中使用 AgentMemory skill 管理长期记忆。
```

全局指令只负责提醒 agent 使用 Skill；具体调用规则由 `agentmemory` Skill 提供。不要在全局指令里写本地 Skill 路径。
