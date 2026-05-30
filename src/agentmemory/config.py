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
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    vector_db_path: Path = DEFAULT_DATA_DIR / "vector"
    vector_table: str = "memory_vectors"
    maintenance_enabled: bool = True
    maintenance_interval_seconds: float = Field(default=10.0, ge=0.1)
    maintenance_limit: int = Field(default=25, ge=1, le=500)
    rest_envelope: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "db_path": str(self.db_path),
            "secret_configured": bool(self.secret),
            "secret": "<redacted>" if self.secret else "",
            "log_level": self.log_level,
            "llm": {
                "provider": "openai-compatible",
                "base_url": self.llm_base_url,
                "model": self.llm_model,
                "api_key_configured": bool(self.llm_api_key),
            },
            "embedding": {
                "provider": "openai-compatible",
                "base_url": self.embedding_base_url,
                "model": self.embedding_model,
                "api_key_configured": bool(self.embedding_api_key),
            },
            "vector": {
                "db_path": str(self.vector_db_path),
                "table": self.vector_table,
            },
            "maintenance": {
                "enabled": self.maintenance_enabled,
                "interval_seconds": self.maintenance_interval_seconds,
                "limit": self.maintenance_limit,
            },
            "rest": {
                "envelope": self.rest_envelope,
            },
        }

    def missing_ai_settings(self) -> list[str]:
        required = {
            "AGENTMEMORY_LLM_BASE_URL": self.llm_base_url,
            "AGENTMEMORY_LLM_API_KEY": self.llm_api_key,
            "AGENTMEMORY_LLM_MODEL": self.llm_model,
            "AGENTMEMORY_EMBEDDING_BASE_URL": self.embedding_base_url,
            "AGENTMEMORY_EMBEDDING_API_KEY": self.embedding_api_key,
            "AGENTMEMORY_EMBEDDING_MODEL": self.embedding_model,
        }
        return [name for name, value in required.items() if not value]


def get_settings() -> Settings:
    return Settings()
