from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func
from app.core import Base


class User(Base):
    """Пользователь платформы (ЕУЗ): контакты, хэш пароля, метаданные и настройки."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=True, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    telegram_id = Column(String, nullable=True)
    notification_settings = Column(JSON, default=lambda: {})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    role = Column(String(20), nullable=False, default="user")
    is_expert = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)