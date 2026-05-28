from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

