"""
إعدادات التطبيق المركزية.
تدعم المتغيرات البيئية، مع قيم افتراضية آمنة للتطوير المحلي.
"""
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
import os

class Settings(BaseSettings):
    # --- قاعدة البيانات (PostgreSQL عبر Supabase أو محلي) ---
    # يستخدم SUPABASE_URL من البيئة إن وُجد، مع إضافة sslmode=require،
    # وإلا يستخدم القيمة الافتراضية للتطوير المحلي.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        os.getenv(
            "SUPABASE_URL",
            "postgresql://ataeru_user:ataeru_password@localhost:5432/ataeru_db"
        )
    )
    # إذا كانت القيمة من SUPABASE_URL، أضف ?sslmode=require
    if DATABASE_URL.startswith("postgresql://") and "?" not in DATABASE_URL:
        if "supabase" in DATABASE_URL.lower():
            DATABASE_URL += "?sslmode=require"

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- الأمان والمصادقة ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-to-a-very-long-random-secret-key-minimum-32-chars")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # --- CORS ---
    BACKEND_CORS_ORIGINS: Union[List[AnyHttpUrl], str] = os.getenv(
        "BACKEND_CORS_ORIGINS",
        ["http://localhost:5173", "http://localhost:3000", "https://*.onrender.com"]
    )

    # --- إعدادات Supabase (للاستخدام المباشر إن لزم) ---
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_JWKS_URL: str = os.getenv("SUPABASE_JWKS_URL", "")

    # --- الذكاء الاصطناعي ---
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")

    # --- الملفات والتحليل ---
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/rfp")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50 MB
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

# إنشاء كائن الإعدادات للاستخدام في جميع أنحاء التطبيق
settings = Settings()
