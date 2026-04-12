"""Асинхронный движок SQLAlchemy и фабрика сессий для FastAPI Depends."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    """Выдаёт асинхронную сессию БД на время обработки запроса."""
    async with AsyncSessionLocal() as session:
        yield session


async def create_db_and_tables() -> None:
    """Создаёт все таблицы для зарегистрированных моделей, если их нет."""
    # Импорт моделей здесь нужен именно при вызове, чтобы избежать циклического импорта.
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
