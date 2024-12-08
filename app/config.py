from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/code_review_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()