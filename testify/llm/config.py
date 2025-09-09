import os

from pydantic import BaseModel, Field


def _env_or_default(name: str, default: str) -> str:
    return os.getenv(name, default)


def _api_key_from_env() -> str | None:
    return os.getenv("TESTIFY_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")


class LLMConfig(BaseModel):
    provider: str = Field(default_factory=lambda: _env_or_default("TESTIFY_LLM_PROVIDER", "openai"))
    model: str = Field(default_factory=lambda: _env_or_default("TESTIFY_LLM_MODEL", "gpt-4o-mini"))
    api_key: str | None = Field(default_factory=_api_key_from_env)
    temperature: float = 0.2
    max_tokens: int = 2000
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls()
