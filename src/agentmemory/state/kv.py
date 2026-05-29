from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import DateTime, Text, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class KVRow(Base):
    __tablename__ = "kv"

    scope: Mapped[str] = mapped_column(Text, primary_key=True)
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StateKV:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            future=True,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self._ensure_fts5()
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)

    def _ensure_fts5(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(
                        document_id UNINDEXED,
                        source_type UNINDEXED,
                        source_id UNINDEXED,
                        session_id UNINDEXED,
                        content,
                        searchable_text,
                        language UNINDEXED,
                        project UNINDEXED,
                        files UNINDEXED,
                        concepts UNINDEXED,
                        created_at UNINDEXED
                    )
                    """,
                ),
            )

    def set(self, scope: str, key: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
        now = utc_now()
        with self._session_factory() as session:
            row = session.get(KVRow, {"scope": scope, "key": key})
            if row is None:
                session.add(
                    KVRow(
                        scope=scope,
                        key=key,
                        value=payload,
                        created_at=now,
                        updated_at=now,
                    ),
                )
            else:
                row.value = payload
                row.updated_at = now
            session.commit()

    def get(self, scope: str, key: str) -> Any | None:
        with self._session_factory() as session:
            row = session.get(KVRow, {"scope": scope, "key": key})
            if row is None:
                return None
            return json.loads(row.value)

    def delete(self, scope: str, key: str) -> bool:
        with self._session_factory() as session:
            row = session.get(KVRow, {"scope": scope, "key": key})
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    def list(self, scope: str) -> list[Any]:
        with self._session_factory() as session:
            rows: Iterable[KVRow] = session.scalars(
                select(KVRow).where(KVRow.scope == scope).order_by(KVRow.key),
            )
            return [json.loads(row.value) for row in rows]

    def probe(self) -> bool:
        with self._session_factory() as session:
            session.execute(select(KVRow).limit(1))
        return True

    def metadata(self, scope: str, key: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            row = session.get(KVRow, {"scope": scope, "key": key})
            if row is None:
                return None
            return {
                "scope": row.scope,
                "key": row.key,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            }

    def fts_upsert(self, document: dict[str, Any]) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("DELETE FROM search_fts WHERE document_id = :document_id"),
                {"document_id": document["id"]},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO search_fts(
                        document_id,
                        source_type,
                        source_id,
                        session_id,
                        content,
                        searchable_text,
                        language,
                        project,
                        files,
                        concepts,
                        created_at
                    )
                    VALUES (
                        :document_id,
                        :source_type,
                        :source_id,
                        :session_id,
                        :content,
                        :searchable_text,
                        :language,
                        :project,
                        :files,
                        :concepts,
                        :created_at
                    )
                    """,
                ),
                {
                    "document_id": document["id"],
                    "source_type": document["sourceType"],
                    "source_id": document["sourceId"],
                    "session_id": document.get("sessionId"),
                    "content": document["content"],
                    "searchable_text": document["searchableText"],
                    "language": document["language"],
                    "project": document.get("project"),
                    "files": json.dumps(document.get("files", []), ensure_ascii=False),
                    "concepts": json.dumps(document.get("concepts", []), ensure_ascii=False),
                    "created_at": document["createdAt"],
                },
            )

    def fts_delete_all(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text("DELETE FROM search_fts"))

    def fts_count(self) -> int:
        with self.engine.begin() as connection:
            return int(connection.execute(text("SELECT COUNT(*) FROM search_fts")).scalar_one())

    def fts_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        document_id,
                        source_type,
                        source_id,
                        session_id,
                        content,
                        searchable_text,
                        language,
                        project,
                        files,
                        concepts,
                        created_at,
                        bm25(search_fts) AS rank
                    FROM search_fts
                    WHERE search_fts MATCH :query
                    ORDER BY rank
                    LIMIT :limit
                    """,
                ),
                {"query": query, "limit": limit},
            ).mappings()
            return [
                {
                    "documentId": row["document_id"],
                    "sourceType": row["source_type"],
                    "sourceId": row["source_id"],
                    "sessionId": row["session_id"],
                    "content": row["content"],
                    "searchableText": row["searchable_text"],
                    "language": row["language"],
                    "project": row["project"],
                    "files": json.loads(row["files"] or "[]"),
                    "concepts": json.loads(row["concepts"] or "[]"),
                    "createdAt": row["created_at"],
                    "score": 1.0 / (1.0 + abs(float(row["rank"] or 0.0))),
                }
                for row in rows
            ]
