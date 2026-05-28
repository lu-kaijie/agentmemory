from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .models import ProviderError, ProviderStatus


class OpenAICompatibleLLMProvider:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.last_error: str | None = None
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            model=self.model,
            baseUrl=self.base_url,
            apiKeyConfigured=bool(self.api_key),
            ready=bool(self.base_url and self.api_key and self.model),
            lastError=self.last_error,
        )

    def summarize(self, text: str, instruction: str | None = None) -> str:
        prompt = instruction or "Summarize the following text concisely."
        return self._complete(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "summarize",
        )

    def extract_memories(self, text: str) -> list[dict[str, Any]]:
        content = self._complete(
            [
                {
                    "role": "system",
                    "content": "Extract stable long-term memory candidates as JSON array.",
                },
                {"role": "user", "content": text},
            ],
            "extract_memories",
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return [{"type": "note", "content": content}]
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            return [parsed]
        return [{"type": "note", "content": content}]

    def explain_search(self, query: str, results: list[dict[str, Any]]) -> str:
        return self._complete(
            [
                {"role": "system", "content": "Explain why these memory search results match the query."},
                {"role": "user", "content": json.dumps({"query": query, "results": results}, ensure_ascii=False)},
            ],
            "explain_search",
        )

    def compress_context(self, items: list[dict[str, Any]], token_budget: int) -> str:
        return self._complete(
            [
                {
                    "role": "system",
                    "content": f"Compress these memory items into context under approximately {token_budget} tokens.",
                },
                {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
            ],
            "compress_context",
        )

    def update_wiki(self, page_title: str, current_content: str, evidence: list[dict[str, Any]]) -> str:
        return self._complete(
            [
                {"role": "system", "content": "Propose a wiki page update based on evidence."},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "pageTitle": page_title,
                            "currentContent": current_content,
                            "evidence": evidence,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "update_wiki",
        )

    def _complete(self, messages: list[dict[str, str]], operation: str) -> str:
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages)
            content = response.choices[0].message.content
            self.last_error = None
            return content or ""
        except Exception as exc:  # pragma: no cover - exercised by real provider failures
            self.last_error = str(exc)
            raise ProviderError("llm", operation, str(exc)) from exc


class OpenAICompatibleEmbeddingProvider:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.last_error: str | None = None
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            model=self.model,
            baseUrl=self.base_url,
            apiKeyConfigured=bool(self.api_key),
            ready=bool(self.base_url and self.api_key and self.model),
            lastError=self.last_error,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self.client.embeddings.create(model=self.model, input=texts)
            self.last_error = None
            return [list(item.embedding) for item in response.data]
        except Exception as exc:  # pragma: no cover - exercised by real provider failures
            self.last_error = str(exc)
            raise ProviderError("embedding", "embed_texts", str(exc)) from exc
