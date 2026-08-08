"""
إعدادات التطبيق المركزية.
"""
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://ataeru_user:ataeru_password@localhost:5432/ataeru_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-to-a-very-long-random-secret-key-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BACKEND_CORS_ORIGINS: Union[List[AnyHttpUrl], str] = ["http://localhost:5173", "http://localhost:3000"]

    # AI
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_PROVIDER: str = "openai"

    # Uploads & analysis
    UPLOAD_DIR: str = "uploads/rfp"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    MAX_RETRIES: int = 3
    CACHE_TTL: int = 3600  # seconds

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return [i.strip() for i in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()