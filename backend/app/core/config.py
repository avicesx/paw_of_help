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

    APP_TIMEZONE: str = Field(
        "Europe/Moscow",
        env="APP_TIMEZONE",
        description="Таймзона приложения для календарных ограничений (например Europe/Moscow)",
    )

    # Кэш редиски
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL", description="URL для Redis")
    FEED_CACHE_TTL: int = Field(300, env="FEED_CACHE_TTL", description="TTL кэша ленты в секундах (по умолчанию 5 мин)")

    # Веса для алгоритма умной ленты (Эвристика)
    WEIGHT_URGENCY: float = Field(50.0, env="WEIGHT_URGENCY", description="Бонус за срочность")
    WEIGHT_DISTANCE: float = Field(20.0, env="WEIGHT_DISTANCE", description="Максимальный балл за близость (0 км)")
    WEIGHT_SKILL: float = Field(15.0, env="WEIGHT_SKILL", description="Бонус за совпадение навыков")
    WEIGHT_FOSTER: float = Field(15.0, env="WEIGHT_FOSTER", description="Бонус за готовность к передержке")
    WEIGHT_TIME: float = Field(10.0, env="WEIGHT_TIME", description="Бонус за совпадение времени")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
