from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
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

    # Image Upload & Storage Configuration
    UPLOAD_DIR: str = "uploads/images"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB default
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    ALLOWED_IMAGE_MIME_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    # OCR Configuration
    OCR_ENGINE: str = "tesseract"
    OCR_LANGUAGE: str = "eng"
    OCR_PSM: int = 6
    OCR_TIMEOUT_SECONDS: int = 30
    TESSERACT_CMD: Optional[str] = None

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

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_token_expire(cls, value: int) -> int:
        if value < 1 or value > 43200:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 43200 (30 days)")
        return value

    @field_validator("MAX_UPLOAD_SIZE_BYTES")
    @classmethod
    def validate_upload_size(cls, value: int) -> int:
        if value < 1024 or value > 52428800:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES must be between 1KB (1024) and 50MB (52428800)")
        return value

    @field_validator("OCR_TIMEOUT_SECONDS")
    @classmethod
    def validate_ocr_timeout(cls, value: int) -> int:
        if value < 1 or value > 300:
            raise ValueError("OCR_TIMEOUT_SECONDS must be between 1 and 300 seconds")
        return value

    @field_validator("OCR_PSM")
    @classmethod
    def validate_ocr_psm(cls, value: int) -> int:
        if value < 0 or value > 13:
            raise ValueError("OCR_PSM must be between 0 and 13")
        return value

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        allowed = ["HS256", "HS384", "HS512"]
        if value.upper() not in allowed:
            raise ValueError(f"JWT_ALGORITHM must be one of {allowed}")
        return value.upper()

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Strictly validate security settings in production environment."""
        if self.ENVIRONMENT.lower() == "production":
            insecure_defaults = [
                "change-this-in-production-secret-key-min-32-chars",
                "secret",
                "changeme",
                "default-secret-key",
            ]
            if self.JWT_SECRET_KEY in insecure_defaults or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "In production, JWT_SECRET_KEY must be configured with a strong secret of at least 32 characters."
                )

            origins = self.get_cors_origins()
            if "*" in origins:
                raise ValueError(
                    "Wildcard CORS origin '*' is strictly prohibited in production environment."
                )
        return self

    def get_cors_origins(self) -> List[str]:
        """Return list of allowed CORS origins."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return self.parse_cors_origins(self.CORS_ORIGINS)


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()