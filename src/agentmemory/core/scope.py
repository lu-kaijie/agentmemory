from __future__ import annotations

import hashlib
import os
from pathlib import Path

from agentmemory.core.ids import utc_now_iso
from agentmemory.core.models import ProjectRecord


def resolve_project_identity(
    cwd: str | None = None,
    project: str | None = None,
    project_id: str | None = None,
    existing: ProjectRecord | None = None,
) -> ProjectRecord:
    now = utc_now_iso()
    root = str(Path(cwd or os.getcwd()).expanduser().resolve())
    name = project or Path(root).name or "project"
    resolved_id = project_id or f"proj_{hashlib.sha256(root.encode('utf-8')).hexdigest()[:24]}"
    if existing:
        existing.name = project or existing.name or name
        existing.root = existing.root or root
        existing.updatedAt = now
        if root not in existing.aliases and existing.root != root:
            existing.aliases.append(root)
        return existing
    return ProjectRecord(
        id=resolved_id,
        name=name,
        root=root,
        aliases=[],
        metadata={},
        createdAt=now,
        updatedAt=now,
    )
