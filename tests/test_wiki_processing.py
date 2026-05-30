from agentmemory.core.wiki import parse_knowledge_xml, parse_wiki_update_xml


def test_parse_wiki_update_xml_valid():
    result = parse_wiki_update_xml(
        '<wiki_update topic="technical_decisions" title="技术决策" confidence="0.82">'
        "<content>项目选择 FastAPI 作为后端。</content>"
        "</wiki_update>",
    )

    assert result == {
        "topic": "technical_decisions",
        "title": "技术决策",
        "content": "项目选择 FastAPI 作为后端。",
        "confidence": 0.82,
    }


def test_parse_wiki_update_xml_rejects_invalid_output():
    assert parse_wiki_update_xml("plain text") is None
    assert parse_wiki_update_xml('<wiki_update topic="unknown"><content>x</content></wiki_update>') is None
    assert parse_wiki_update_xml('<wiki_update topic="technical_decisions"></wiki_update>') is None


def test_parse_knowledge_xml_valid_items():
    result = parse_knowledge_xml(
        "<knowledge>"
        '<item kind="semantic" confidence="0.8"><content>Use FastAPI.</content><concepts>api,backend</concepts></item>'
        '<item kind="lesson" confidence="0.7"><content>Repair indexes after schema changes.</content></item>'
        "</knowledge>",
    )

    assert result == [
        {
            "kind": "semantic",
            "content": "Use FastAPI.",
            "confidence": 0.8,
            "concepts": ["api", "backend"],
            "files": [],
        },
        {
            "kind": "lesson",
            "content": "Repair indexes after schema changes.",
            "confidence": 0.7,
            "concepts": [],
            "files": [],
        },
    ]


def test_parse_knowledge_xml_rejects_invalid_items():
    assert parse_knowledge_xml("<knowledge/>") == []
    assert parse_knowledge_xml('<item kind="unknown"><content>x</content></item>') == []
    assert parse_knowledge_xml('<item kind="semantic"></item>') == []
