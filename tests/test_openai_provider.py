import pytest

from agentmemory.config import Settings
from agentmemory.providers import OpenAICompatibleEmbeddingProvider, OpenAICompatibleLLMProvider


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
