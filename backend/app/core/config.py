from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Travio AI Backend"
    API_V1_PREFIX: str = "/api/v1"
    VERSION: str = "1.0.0"
    TESTING: bool = False

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:3000",
        "http://127.0.0.1:8081",
        "*",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Supabase Auth Configuration
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_AUDIENCE: str = "authenticated"
    SUPABASE_JWKS_URL: Optional[str] = None

    @property
    def supabase_issuer(self) -> Optional[str]:
        if self.SUPABASE_URL:
            clean_url = self.SUPABASE_URL.rstrip("/")
            return f"{clean_url}/auth/v1"
        return None

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/travio_db"
    DATABASE_ECHO: bool = False

    # External Provider Credentials (Milestone 4)
    GEOAPIFY_API_KEY: str = ""
    AMADEUS_API_KEY: str = ""
    AMADEUS_API_SECRET: str = ""
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
