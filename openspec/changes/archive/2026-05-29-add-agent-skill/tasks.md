## 1. Skill Structure

- [x] 1.1 Create `skills/agentmemory/SKILL.md`
- [x] 1.2 Add YAML frontmatter with `name: agentmemory` and a precise Chinese-compatible description
- [x] 1.3 Keep the Skill body concise and Chinese, with command names and API paths in English
- [x] 1.4 Document the one-line global agent configuration text without a local Skill path

## 2. Skill Behavior Guidance

- [x] 2.1 Document CLI-first and REST-fallback usage
- [x] 2.2 Document when agent must search memory before acting
- [x] 2.3 Document when agent should use `observe`
- [x] 2.4 Document when agent should use `remember`
- [x] 2.5 Document search mode selection: keyword, vector, hybrid, and smart-search
- [x] 2.6 Document index status/repair/rebuild guidance
- [x] 2.7 Document low-frequency usage rules to avoid slowing current agent work
- [x] 2.8 Exclude Hook, MCP, context, wiki, export, delete, and other unsupported operations

## 3. Validation

- [x] 3.1 Add tests that validate Skill file existence and frontmatter
- [x] 3.2 Add tests that validate required CLI/REST guidance appears
- [x] 3.3 Add tests that unsupported operations are not advertised
- [x] 3.4 Add tests that global configuration guidance mentions Skill name without a local path
- [x] 3.5 Run skill validation with the skill-creator validation script if available
- [x] 3.6 Run full pytest suite
- [x] 3.7 Verify OpenSpec status is complete for `add-agent-skill`
