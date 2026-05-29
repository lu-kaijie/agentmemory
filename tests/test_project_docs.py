from pathlib import Path


def test_project_docs_include_low_frequency_llm_processing_guidance():
    text = Path("PROJECT.md").read_text(encoding="utf-8")

    assert "LLM-required but low-frequency" in text
    assert "Skill 不允许要求 agent 在每次工具调用" in text
    assert "hook 默认只记录轻量原始事件" in text
