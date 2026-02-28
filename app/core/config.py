from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    max_topics: int = 12
    max_decisions: int = 30
    max_actions: int = 50
    max_insights: int = 50
    similarity_threshold: float = 0.65

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
