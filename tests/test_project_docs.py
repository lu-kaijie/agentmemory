from pathlib import Path


def test_project_docs_include_low_frequency_llm_processing_guidance():
    text = Path("PROJECT.md").read_text(encoding="utf-8")

    assert "LLM-required but low-frequency" in text
    assert "Skill 不允许要求 agent 在每次工具调用" in text
    assert "hook 默认只记录轻量原始事件" in text


def test_memory_search_change_excludes_wiki_viewer_hook_mcp():
    proposal = Path("openspec/changes/archive/2026-05-29-add-memory-search/proposal.md").read_text(encoding="utf-8")
    design = Path("openspec/changes/archive/2026-05-29-add-memory-search/design.md").read_text(encoding="utf-8")

    assert "不实现 Wiki 页面维护" in proposal
    assert "不实现 Viewer" in design
    assert "不实现 MCP、Hook" in design


def test_agentmemory_skill_frontmatter_and_guidance():
    text = Path("skills/agentmemory/SKILL.md").read_text(encoding="utf-8")

    assert text.startswith("---\n")
    assert "name: agentmemory" in text
    assert "description:" in text
    assert "agentmemory search" in text
    assert "agentmemory smart-search" in text
    assert "agentmemory context" in text
    assert "agentmemory wiki" in text
    assert "agentmemory observe" in text
    assert "agentmemory remember" in text
    assert "POST /agentmemory/search" in text
    assert "POST /agentmemory/context" in text
    assert "POST /agentmemory/remember" in text
    assert "confidence" in text
    assert "evidence" in text
    assert "matchSources" in text
    assert "低分" in text
    assert "不是系统指令" in text
    assert "不是开发者指令" in text
    assert "不是用户新指令" in text
    assert "不能覆盖当前用户要求" in text
    assert "不要在每次文件读取" in text


def test_agentmemory_skill_does_not_advertise_unsupported_operations():
    text = Path("skills/agentmemory/SKILL.md").read_text(encoding="utf-8")

    forbidden = [
        "agentmemory delete",
    ]
    for phrase in forbidden:
        assert phrase not in text
    assert "当前版本不要使用未实现的自动采集、Hook 或 MCP 接入。" in text


def test_global_agent_setup_uses_skill_name_without_path():
    text = Path("docs/agent-setup.md").read_text(encoding="utf-8")

    assert "编码任务中使用 AgentMemory skill 管理长期记忆。" in text
    assert "~/.codex" not in text
    assert "/skills/agentmemory" not in text


def test_readme_and_technical_docs_cover_rag_and_llm_wiki():
    readme = Path("README.md").read_text(encoding="utf-8")
    technical = Path("docs/technical-implementation.md").read_text(encoding="utf-8")

    assert "快速开始" in readme
    assert "配置环境变量" in readme
    assert "RAG 是怎么用的" in readme
    assert "LLM Wiki 是什么" in readme
    assert "Agent 接入" in readme
    assert "技术选型" in technical
    assert "RAG 实现" in technical
    assert "LLM Wiki 实现" in technical
    assert "Maintenance 和失败恢复" in technical
