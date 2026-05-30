from __future__ import annotations

import json
import re
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
                    "content": (
                        "Extract stable long-term memory candidates. "
                        "Prefer this XML-like format:\n"
                        "<memories>\n"
                        '<memory type="fact" confidence="0.8">\n'
                        "<content>Durable fact to remember.</content>\n"
                        "<concepts>comma,separated,concepts</concepts>\n"
                        "<files>comma,separated,files</files>\n"
                        "</memory>\n"
                        "</memories>\n"
                        "If there are no durable memories, output <memories/>."
                    ),
                },
                {"role": "user", "content": text},
            ],
            "extract_memories",
        )
        return _parse_memory_xml(content)

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

    def update_wiki(
        self,
        topic: str,
        page_title: str,
        current_content: str,
        evidence: list[dict[str, Any]],
    ) -> str:
        return self._complete(
            [
                {
                    "role": "system",
                    "content": (
                        "Update one AgentMemory Wiki page using only the provided evidence. "
                        "Return exactly this XML-like format:\n"
                        '<wiki_update topic="technical_decisions" title="技术决策" confidence="0.8">\n'
                        "<content>Updated page content with concise durable knowledge.</content>\n"
                        "</wiki_update>\n"
                        "Use the requested topic. If evidence is insufficient, still return a short "
                        "page update grounded in the evidence."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "topic": topic,
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

    def distill_knowledge(self, evidence: list[dict[str, Any]]) -> str:
        return self._complete(
            [
                {
                    "role": "system",
                    "content": (
                        "Distill durable AgentMemory knowledge from evidence. "
                        "Return only XML-like output in this format:\n"
                        "<knowledge>\n"
                        '<item kind="semantic" confidence="0.8">\n'
                        "<content>Stable fact.</content>\n"
                        "<concepts>comma,separated,concepts</concepts>\n"
                        "<files>comma,separated,files</files>\n"
                        "</item>\n"
                        '<item kind="procedural" confidence="0.8"><content>Workflow or habit.</content></item>\n'
                        '<item kind="lesson" confidence="0.8"><content>Lesson to remember.</content></item>\n'
                        '<item kind="crystal" confidence="0.8"><content>Concise work digest.</content></item>\n'
                        "</knowledge>\n"
                        "Allowed kind values: semantic, procedural, lesson, crystal. "
                        "Use only evidence-grounded knowledge. If nothing durable exists, output <knowledge/>."
                    ),
                },
                {"role": "user", "content": json.dumps({"evidence": evidence}, ensure_ascii=False)},
            ],
            "distill_knowledge",
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


def _parse_memory_xml(content: str) -> list[dict[str, Any]]:
    if "<memories/>" in content or "<no-memory/>" in content:
        return []

    items: list[dict[str, Any]] = []
    memory_regex = re.compile(r"<memory\b([^>]*)>([\s\S]*?)</memory>", re.IGNORECASE)
    for match in memory_regex.finditer(content):
        attrs = match.group(1)
        body = match.group(2)
        memory_content = _tag_text(body, "content") or body.strip()
        if not memory_content:
            continue
        items.append(
            {
                "type": _attr_value(attrs, "type") or "fact",
                "confidence": _attr_value(attrs, "confidence"),
                "content": memory_content,
                "concepts": _csv_values(_tag_text(body, "concepts")),
                "files": _csv_values(_tag_text(body, "files")),
            },
        )
    return items


def _attr_value(attrs: str, name: str) -> str | None:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', attrs, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _tag_text(content: str, tag: str) -> str | None:
    match = re.search(rf"<{re.escape(tag)}>([\s\S]*?)</{re.escape(tag)}>", content, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _csv_values(content: str | None) -> list[str]:
    if not content:
        return []
    return [item.strip() for item in content.split(",") if item.strip()]
