"""Core application configuration and settings."""

import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Application
    APP_NAME: str = "FraudLens AI — Financial Fraud & Risk Detection"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/fraud_detection_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Security / JWT
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Initial Dev Seed Credentials (for local environment setup only)
    INITIAL_ADMIN_EMAIL: str = "admin@fraudlens.internal"
    INITIAL_ADMIN_PASSWORD: str = "AdminSecure@2026!"
    INITIAL_INVESTIGATOR_EMAIL: str = "investigator@fraudlens.internal"
    INITIAL_INVESTIGATOR_PASSWORD: str = "Investigator@2026!"

    # LLM API Keys (Google Gemini + xAI Grok)
    GEMINI_API_KEY: str = ""
    GROK_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "gemini"  # 'gemini' | 'grok'

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []


settings = Settings()
