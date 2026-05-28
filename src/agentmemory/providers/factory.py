from __future__ import annotations

from dataclasses import dataclass

from agentmemory.config import Settings

from .models import ProviderStatus
from .openai_compatible import OpenAICompatibleEmbeddingProvider, OpenAICompatibleLLMProvider
from .protocols import EmbeddingProvider, LLMProvider


class MissingAIProviderSettings(RuntimeError):
    def __init__(self, missing_settings: list[str]):
        self.missing_settings = missing_settings
        joined = ", ".join(missing_settings)
        super().__init__(f"Missing required AI provider settings: {joined}")


@dataclass(frozen=True)
class ProviderBundle:
    llm: LLMProvider
    embedding: EmbeddingProvider

    def health_summary(self) -> dict[str, object]:
        return {
            "llm": self.llm.status().model_dump(),
            "embedding": self.embedding.status().model_dump(),
        }


def require_ai_settings(settings: Settings) -> None:
    missing = settings.missing_ai_settings()
    if missing:
        raise MissingAIProviderSettings(missing)


def create_provider_bundle(settings: Settings) -> ProviderBundle:
    require_ai_settings(settings)
    return ProviderBundle(
        llm=OpenAICompatibleLLMProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        ),
        embedding=OpenAICompatibleEmbeddingProvider(
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key,
            model=settings.embedding_model,
        ),
    )


def missing_provider_status(name: str, model: str, base_url: str, api_key: str, missing: list[str]) -> ProviderStatus:
    return ProviderStatus(
        provider="openai-compatible",
        model=model,
        baseUrl=base_url,
        apiKeyConfigured=bool(api_key),
        ready=False,
        lastError=f"Missing required settings: {', '.join(missing)}" if missing else None,
        missingSettings=missing,
    )
