from __future__ import annotations

from typing import Any, Protocol

from .models import ProviderStatus


class LLMProvider(Protocol):
    def status(self) -> ProviderStatus:
        ...

    def summarize(self, text: str, instruction: str | None = None) -> str:
        ...

    def extract_memories(self, text: str) -> list[dict[str, Any]]:
        ...

    def explain_search(self, query: str, results: list[dict[str, Any]]) -> str:
        ...

    def compress_context(self, items: list[dict[str, Any]], token_budget: int) -> str:
        ...

    def update_wiki(
        self,
        topic: str,
        page_title: str,
        current_content: str,
        evidence: list[dict[str, Any]],
    ) -> str:
        ...

    def distill_knowledge(self, evidence: list[dict[str, Any]]) -> str:
        ...


class EmbeddingProvider(Protocol):
    def status(self) -> ProviderStatus:
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...
