from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderError(RuntimeError):
    def __init__(self, provider: str, operation: str, message: str):
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "message": self.message,
        }


class ProviderStatus(BaseModel):
    provider: str = "openai-compatible"
    model: str
    baseUrl: str
    apiKeyConfigured: bool
    ready: bool
    lastError: str | None = None
    missingSettings: list[str] = Field(default_factory=list)
