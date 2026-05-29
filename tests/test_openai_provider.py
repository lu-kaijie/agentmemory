import pytest

from agentmemory.config import Settings
from agentmemory.providers import OpenAICompatibleEmbeddingProvider, OpenAICompatibleLLMProvider
from agentmemory.providers.openai_compatible import _parse_memory_xml


def _required_setting(settings: Settings, env_name: str, field_name: str) -> str:
    value = getattr(settings, field_name)
    if not value:
        pytest.fail(f"{env_name} must be configured for real provider tests")
    return value


def test_real_llm_provider_summarize_call():
    settings = Settings()
    provider = OpenAICompatibleLLMProvider(
        base_url=_required_setting(settings, "AGENTMEMORY_LLM_BASE_URL", "llm_base_url"),
        api_key=_required_setting(settings, "AGENTMEMORY_LLM_API_KEY", "llm_api_key"),
        model=_required_setting(settings, "AGENTMEMORY_LLM_MODEL", "llm_model"),
    )

    summary = provider.summarize(
        "AgentMemory stores long-term memory for coding agents.",
        "Return a short summary in one sentence.",
    )

    assert summary.strip()
    assert provider.status().lastError is None


def test_real_embedding_provider_embed_texts_call():
    settings = Settings()
    provider = OpenAICompatibleEmbeddingProvider(
        base_url=_required_setting(settings, "AGENTMEMORY_EMBEDDING_BASE_URL", "embedding_base_url"),
        api_key=_required_setting(settings, "AGENTMEMORY_EMBEDDING_API_KEY", "embedding_api_key"),
        model=_required_setting(settings, "AGENTMEMORY_EMBEDDING_MODEL", "embedding_model"),
    )

    vectors = provider.embed_texts(["AgentMemory requires real AI providers."])

    assert len(vectors) == 1
    assert vectors[0]
    assert all(isinstance(value, float) for value in vectors[0])
    assert provider.status().lastError is None


def test_parse_memory_xml_candidates():
    items = _parse_memory_xml(
        """
        <memories>
          <memory type="decision" confidence="0.82">
            <content>Use XML-like memory extraction output before JSON fallback.</content>
            <concepts>llm-output, parsing</concepts>
            <files>src/agentmemory/providers/openai_compatible.py</files>
          </memory>
        </memories>
        """,
    )

    assert items == [
        {
            "type": "decision",
            "confidence": "0.82",
            "content": "Use XML-like memory extraction output before JSON fallback.",
            "concepts": ["llm-output", "parsing"],
            "files": ["src/agentmemory/providers/openai_compatible.py"],
        },
    ]


def test_parse_memory_xml_empty_candidates():
    assert _parse_memory_xml("<memories/>") == []


def test_parse_memory_xml_ignores_json_candidates():
    assert _parse_memory_xml('[{"type":"fact","content":"Do not parse JSON here."}]') == []
