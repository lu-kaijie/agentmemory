from pathlib import Path


def test_project_docs_include_low_frequency_llm_processing_guidance():
    text = Path("PROJECT.md").read_text(encoding="utf-8")

    assert "LLM-required but low-frequency" in text
    assert "Skill 不允许要求 agent 在每次工具调用" in text
    assert "hook 默认只记录轻量原始事件" in text


def test_memory_search_change_excludes_wiki_viewer_hook_mcp():
    proposal = Path("openspec/changes/add-memory-search/proposal.md").read_text(encoding="utf-8")
    design = Path("openspec/changes/add-memory-search/design.md").read_text(encoding="utf-8")

    assert "不实现 Wiki 页面维护" in proposal
    assert "不实现 Viewer" in design
    assert "不实现 MCP、Hook" in design
