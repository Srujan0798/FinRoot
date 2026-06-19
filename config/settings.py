"""Typed settings loader backed by pydantic-settings (12-Factor env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: str = "mock"  # one of: mock | ollama | groq | openai (Provider enum values)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    chroma_dir: str = "data/chroma"
    audit_path: str = "logs/audit.jsonl"

    model_config = SettingsConfigDict(env_prefix="FINROOT_")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
