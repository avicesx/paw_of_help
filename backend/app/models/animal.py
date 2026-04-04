from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, JSON, String, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Animal(Base):
    __tablename__ = "animals"

    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(
        Enum("organization", "private", name="animal_owner_type"),
        nullable=False,
    )
    owner_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    photos = Column(JSON, default=lambda: [])
    description = Column(Text, nullable=True)
    species = Column(String(255), nullable=True)
    breed = Column(String(255), nullable=True)
    age = Column(String(50), nullable=True)
    gender = Column(String(10), nullable=True)
    size = Column(String(50), nullable=True)
    character = Column(Text, nullable=True)
    health_status = Column(Text, nullable=True)
    special_needs = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="needs_home")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())