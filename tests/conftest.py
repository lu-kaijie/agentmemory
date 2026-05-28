from pathlib import Path

from agentmemory.config import Settings


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
