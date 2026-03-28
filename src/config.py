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

    model_config = {
        "env_file": "/Users/swarajnaik/Desktop/11/.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
