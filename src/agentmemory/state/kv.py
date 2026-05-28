from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import DateTime, Text, create_engine, select
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
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)

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

