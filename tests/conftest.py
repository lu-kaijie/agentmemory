from pathlib import Path
from typing import Any

from agentmemory.config import Settings
from agentmemory.providers.models import ProviderStatus


def ai_settings(db_path: Path) -> Settings:
    return Settings(
        db_path=db_path,
        llm_base_url="https://api.openai.com/v1",
        llm_api_key="test-llm-key",
        llm_model="gpt-test",
        embedding_base_url="https://api.openai.com/v1",
        embedding_api_key="test-embedding-key",
        embedding_model="text-embedding-test",
    )


class StubLLMProvider:
    def __init__(
        self,
        summary: str = "Stub summary",
        candidates: list[dict[str, Any]] | None = None,
        fail: bool = False,
    ):
        self.summary = summary
        self.candidates = candidates if candidates is not None else [
            {
                "type": "decision",
                "content": "Remember the tested memory processing behavior.",
                "confidence": 0.9,
                "concepts": ["memory-processing"],
                "files": ["src/agentmemory/core/service.py"],
            },
        ]
        self.fail = fail

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            model="stub",
            baseUrl="stub://llm",
            apiKeyConfigured=True,
            ready=True,
        )

    def summarize(self, text: str, instruction: str | None = None) -> str:
        if self.fail:
            raise RuntimeError("stub llm failure")
        return self.summary

    def extract_memories(self, text: str) -> list[dict[str, Any]]:
        if self.fail:
            raise RuntimeError("stub llm failure")
        return self.candidates

    def explain_search(self, query: str, results: list[dict[str, Any]]) -> str:
        return "stub explanation"

    def compress_context(self, items: list[dict[str, Any]], token_budget: int) -> str:
        return "stub context"

    def update_wiki(self, page_title: str, current_content: str, evidence: list[dict[str, Any]]) -> str:
        return "stub wiki update"


class StubEmbeddingProvider:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            model="stub-embedding",
            baseUrl="stub://embedding",
            apiKeyConfigured=True,
            ready=True,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.fail:
            raise RuntimeError("stub embedding failure")
        return [_vector_for_text(text) for text in texts]


def _vector_for_text(text: str) -> list[float]:
    lower = text.lower()
    return [
        float(len(lower) % 17) / 17.0,
        1.0 if "fastapi" in lower else 0.0,
        1.0 if "llm" in lower or "memory" in lower else 0.0,
        1.0 if "search" in lower or "rag" in lower else 0.0,
    ]
