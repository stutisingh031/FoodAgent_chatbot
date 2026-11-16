
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Food Support Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = (
        "mysql+pymysql://root:password@localhost:3306/food_support"
    )

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Authentication settings
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        # Resolve the project's .env from this file so launching Uvicorn from
        # the repository root, backend/, or through --app-dir uses one config.
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
