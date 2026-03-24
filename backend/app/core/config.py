"""Загрузка настроек из переменных окружения и `.env`."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения (БД, JWT, опции SQLAlchemy)."""

    DATABASE_URL: str = Field(..., description="Async SQLAlchemy URL, например postgresql+asyncpg://...")
    SECRET_KEY: str = Field(..., alias="JWT_SECRET_KEY", description="Секрет для подписи JWT")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    DATABASE_ECHO: bool = Field(False, env="DATABASE_ECHO", description="Логировать SQL (только для отладки)")
    CORS_ORIGINS: str = Field(
        "",
        env="CORS_ORIGINS",
        description="Список origin через запятую. Пусто или * — разрешить любой origin (без credentials)",
    )
    AUTH_RATE_LIMIT: str = Field(
        "10/minute",
        env="AUTH_RATE_LIMIT",
        description="Лимит slowapi для POST /auth/login и /auth/register (например 10/minute)",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
