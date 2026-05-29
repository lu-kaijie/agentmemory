## 1. Skill Structure

- [ ] 1.1 Create `skills/agentmemory/SKILL.md`
- [ ] 1.2 Add YAML frontmatter with `name: agentmemory` and a precise Chinese-compatible description
- [ ] 1.3 Keep the Skill body concise and Chinese, with command names and API paths in English

## 2. Skill Behavior Guidance

- [ ] 2.1 Document CLI-first and REST-fallback usage
- [ ] 2.2 Document when agent must search memory before acting
- [ ] 2.3 Document when agent should use `observe`
- [ ] 2.4 Document when agent should use `remember`
- [ ] 2.5 Document search mode selection: keyword, vector, hybrid, and smart-search
- [ ] 2.6 Document index status/repair/rebuild guidance
- [ ] 2.7 Document low-frequency usage rules to avoid slowing current agent work
- [ ] 2.8 Exclude Hook, MCP, context, wiki, export, delete, and other unsupported operations

## 3. Validation

- [ ] 3.1 Add tests that validate Skill file existence and frontmatter
- [ ] 3.2 Add tests that validate required CLI/REST guidance appears
- [ ] 3.3 Add tests that unsupported operations are not advertised
- [ ] 3.4 Run skill validation with the skill-creator validation script if available
- [ ] 3.5 Run full pytest suite
- [ ] 3.6 Verify OpenSpec status is complete for `add-agent-skill`
