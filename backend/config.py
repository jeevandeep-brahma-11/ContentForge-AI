from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    firecrawl_api_key: str = ""

    database_url: str = "sqlite+aiosqlite:///./contentforge.db"

    trends_refresh_minutes: int = 60
    trends_niches: str = "ai tools,productivity"

    max_feedback_loops: int = 2

    @property
    def niches(self) -> list[str]:
        return [n.strip() for n in self.trends_niches.split(",") if n.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
