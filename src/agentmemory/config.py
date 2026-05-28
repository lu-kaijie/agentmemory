from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DATA_DIR = Path.home() / ".agentmemory"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTMEMORY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = Field(default=3111, ge=1, le=65535)
    db_path: Path = DEFAULT_DATA_DIR / "agentmemory.sqlite3"
    secret: str = ""
    log_level: str = "INFO"

    def safe_summary(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "db_path": str(self.db_path),
            "secret_configured": bool(self.secret),
            "secret": "<redacted>" if self.secret else "",
            "log_level": self.log_level,
        }


def get_settings() -> Settings:
    return Settings()

