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

    def update_wiki(
        self,
        topic: str,
        page_title: str,
        current_content: str,
        evidence: list[dict[str, Any]],
    ) -> str:
        return (
            f'<wiki_update topic="{topic}" title="{page_title or "Stub Wiki"}" confidence="0.9">'
            "<content>Stub wiki update</content>"
            "</wiki_update>"
        )

    def distill_knowledge(self, evidence: list[dict[str, Any]]) -> str:
        return (
            "<knowledge>"
            '<item kind="semantic" confidence="0.9">'
            "<content>Stub semantic knowledge</content>"
            "<concepts>wiki,knowledge</concepts>"
            "</item>"
            '<item kind="procedural" confidence="0.8">'
            "<content>Stub procedural pattern</content>"
            "</item>"
            '<item kind="lesson" confidence="0.7">'
            "<content>Stub lesson</content>"
            "</item>"
            '<item kind="crystal" confidence="0.6">'
            "<content>Stub crystal digest</content>"
            "</item>"
            "</knowledge>"
        )

    def consolidate_wiki(self, evidence: list[dict[str, Any]], existing: list[dict[str, Any]]) -> str:
        return (
            "<consolidation>"
            "<knowledge>"
            '<item kind="semantic" confidence="0.91">'
            "<content>Strong LLM semantic consolidation.</content>"
            "<concepts>wiki,llm</concepts>"
            "</item>"
            '<item kind="procedural" confidence="0.86">'
            "<content>Strong LLM procedural consolidation.</content>"
            "</item>"
            "</knowledge>"
            '<page type="concept" title="LLM Wiki Consolidation" slug="llm-wiki-consolidation" topic="project_overview" confidence="0.88">'
            "<content>Dynamic page from strong LLM consolidation.</content>"
            "<sourceIds>memory:mem_stub</sourceIds>"
            "<concepts>wiki,llm</concepts>"
            "</page>"
            '<issue type="stale" severity="warning">'
            "<message>Stub stale issue</message>"
            "<sourceIds>knowledge:old</sourceIds>"
            "<suggestedAction>Review stale claim.</suggestedAction>"
            "</issue>"
            "</consolidation>"
        )

    def lint_wiki(self, records: list[dict[str, Any]]) -> str:
        return (
            "<issues>"
            '<issue type="contradiction" severity="warning">'
            "<message>Stub contradiction detected by LLM lint.</message>"
            "<sourceIds>knowledge:a,knowledge:b</sourceIds>"
            "<suggestedAction>Resolve the conflicting claims.</suggestedAction>"
            "</issue>"
            "</issues>"
        )

    def update_project_profile(
        self,
        project: dict[str, Any],
        existing: dict[str, Any] | None,
        evidence: list[dict[str, Any]],
    ) -> str:
        return (
            '{"content":"Stub project profile","goals":["test AgentMemory"],'
            '"techStack":["python"],"keyFiles":["src/agentmemory/core/service.py"],'
            '"commands":["uv run pytest"],"conventions":["use scoped context"],'
            '"risks":["stale evidence"],"confidence":0.9}'
        )


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
