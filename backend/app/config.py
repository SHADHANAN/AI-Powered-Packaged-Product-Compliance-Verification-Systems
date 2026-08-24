from functools import lru_cache
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    # Application Information
    APP_NAME: str = "AI-Powered Packaged Product Compliance Verification System"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Production-oriented API backend for automated packaged product compliance verification."
    )
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Routing
    API_PREFIX: str = "/api"

    # CORS Origins (supports comma-separated string or list)
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database Configuration
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/product_compliance"

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = "change-this-in-production-secret-key-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[List[str], str]) -> List[str]:
        """Parse comma-separated string or list of origins into a list of strings."""
        if isinstance(value, str):
            if not value.strip():
                return []
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        elif isinstance(value, (list, tuple, set)):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return []

    def get_cors_origins(self) -> List[str]:
        """Return list of allowed CORS origins."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return self.parse_cors_origins(self.CORS_ORIGINS)


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
