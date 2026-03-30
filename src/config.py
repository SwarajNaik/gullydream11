from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5436/gullydream11"
    REDIS_URL: str = "redis://localhost:6380/0"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_BASE_URL: str = "http://localhost:8000"
    DEBUG: bool = True
    REQUEST_TIMEOUT_SECONDS: int = 30

    # JWT Auth
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Admin
    ADMIN_EMAILS: str = "admin@gullydream11.com"

    # Cricket Data API (cricketdata.org / cricapi.com)
    CRICKET_API_KEY: str = ""
    CRICKET_API_URL: str = "https://api.cricapi.com/v1"

    # App
    APP_NAME: str = "GullyDream11"

    # Production Configuration
    FRONTEND_URL: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"  # development, staging, production
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # text for dev, json for production

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Enforce security constraints in production."""
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY == "your-secret-key-change-in-production":
                raise ValueError(
                    "JWT_SECRET_KEY must not be the default value in production"
                )
            if self.DEBUG is True:
                raise ValueError("DEBUG must be False in production")
            if "localhost" in self.FRONTEND_URL:
                raise ValueError("FRONTEND_URL must not contain 'localhost' in production")
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
