from __future__ import annotations

import re
from typing import Any

from agentmemory.core.models import WIKI_TOPICS, WikiTopic


WIKI_TITLES: dict[WikiTopic, str] = {
    "personal_preferences": "个人偏好",
    "project_overview": "项目概览",
    "technical_decisions": "技术决策",
    "troubleshooting": "常见问题和修复经验",
    "files_and_modules": "文件和模块说明",
    "workflow_habits": "工作流习惯",
}


def parse_wiki_update_xml(content: str) -> dict[str, Any] | None:
    match = re.search(r"<wiki_update\b([^>]*)>([\s\S]*?)</wiki_update>", content, re.IGNORECASE)
    if not match:
        return None
    attrs = match.group(1)
    body = match.group(2)
    topic = _attr_value(attrs, "topic")
    if topic not in WIKI_TOPICS:
        return None
    update_content = _tag_text(body, "content") or body.strip()
    if not update_content:
        return None
    title = _attr_value(attrs, "title") or WIKI_TITLES[topic]  # type: ignore[index]
    return {
        "topic": topic,
        "title": title,
        "content": update_content,
        "confidence": _coerce_confidence(_attr_value(attrs, "confidence")),
    }


def parse_knowledge_xml(content: str) -> list[dict[str, Any]]:
    if "<knowledge/>" in content or "<no-knowledge/>" in content:
        return []
    records: list[dict[str, Any]] = []
    for match in re.finditer(r"<item\b([^>]*)>([\s\S]*?)</item>", content, re.IGNORECASE):
        attrs = match.group(1)
        body = match.group(2)
        kind = _attr_value(attrs, "kind")
        if kind not in ("semantic", "procedural", "lesson", "crystal"):
            continue
        record_content = _tag_text(body, "content") or body.strip()
        if not record_content:
            continue
        records.append(
            {
                "kind": kind,
                "content": record_content,
                "confidence": _coerce_confidence(_attr_value(attrs, "confidence")),
                "concepts": _csv_values(_tag_text(body, "concepts")),
                "files": _csv_values(_tag_text(body, "files")),
            },
        )
    return records


def parse_wiki_consolidation_xml(content: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "knowledge": parse_knowledge_xml(content),
        "pages": parse_dynamic_pages_xml(content),
        "issues": parse_lint_xml(content),
    }


def parse_dynamic_pages_xml(content: str) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for match in re.finditer(r"<page\b([^>]*)>([\s\S]*?)</page>", content, re.IGNORECASE):
        attrs = match.group(1)
        body = match.group(2)
        page_type = _attr_value(attrs, "type") or "synthesis"
        if page_type not in ("entity", "concept", "source", "comparison", "synthesis", "topic"):
            continue
        title = _attr_value(attrs, "title") or "Untitled"
        topic = _attr_value(attrs, "topic") or "project_overview"
        if topic not in WIKI_TOPICS:
            topic = "project_overview"
        page_content = _tag_text(body, "content") or body.strip()
        if not page_content:
            continue
        pages.append(
            {
                "type": page_type,
                "title": title,
                "topic": topic,
                "slug": _attr_value(attrs, "slug") or _slugify(title),
                "content": page_content,
                "confidence": _coerce_confidence(_attr_value(attrs, "confidence")),
                "sourceIds": _csv_values(_tag_text(body, "sourceIds")),
                "concepts": _csv_values(_tag_text(body, "concepts")),
            },
        )
    return pages


def parse_lint_xml(content: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for match in re.finditer(r"<issue\b([^>]*)>([\s\S]*?)</issue>", content, re.IGNORECASE):
        attrs = match.group(1)
        body = match.group(2)
        issue_type = _attr_value(attrs, "type")
        if issue_type not in ("contradiction", "stale", "low_confidence", "missing_source", "orphan"):
            continue
        severity = _attr_value(attrs, "severity") or "warning"
        if severity not in ("info", "warning", "error"):
            severity = "warning"
        message = _tag_text(body, "message") or body.strip()
        if not message:
            continue
        issues.append(
            {
                "type": issue_type,
                "severity": severity,
                "message": message,
                "sourceIds": _csv_values(_tag_text(body, "sourceIds")),
                "suggestedAction": _tag_text(body, "suggestedAction") or "",
            },
        )
    return issues


def _attr_value(attrs: str, name: str) -> str | None:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', attrs, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _tag_text(content: str, tag: str) -> str | None:
    match = re.search(rf"<{re.escape(tag)}>([\s\S]*?)</{re.escape(tag)}>", content, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _coerce_confidence(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except ValueError:
        return None
    return max(0.0, min(1.0, numeric))


def _csv_values(content: str | None) -> list[str]:
    if not content:
        return []
    return [item.strip() for item in content.split(",") if item.strip()]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value.strip().casefold()).strip("-")
    return slug[:80] or "page"
