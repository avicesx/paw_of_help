from sqlalchemy import Column, DateTime, Enum, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from typing import Literal

AnimalOwnerType = Literal["private", "organization"]
AnimalGender = Literal["male", "female", "unknown"]
AnimalSize = Literal["small", "medium", "large", "extra_large"]
AnimalStatus = Literal["needs_home", "on_treatment", "on_adaptation", "adopted", "deceased"]

class Animal(Base):
    __tablename__ = "animals"

    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(
        Enum("private", "organization", name="animal_owner_type"),
        nullable=False,
        index=True,
    )
    owner_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    photos = Column(JSON, default=lambda: [])
    description = Column(Text, nullable=True)
    species = Column(String(255), nullable=True)
    breed = Column(String(255), nullable=True)
    age = Column(String(50), nullable=True)
    gender = Column(
        Enum("male", "female", "unknown", name="animal_gender"),
        nullable=True,
    )
    size = Column(
        Enum("small", "medium", "large", "extra_large", name="animal_size"),
        nullable=True,
    )
    character = Column(Text, nullable=True)
    health_status = Column(Text, nullable=True)
    special_needs = Column(Text, nullable=True)
    status = Column(
        Enum(
            "needs_home",
            "on_treatment",
            "on_adaptation",
            "adopted",
            "deceased",
            name="animal_status",
        ),
        nullable=False,
        default="needs_home",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tasks = relationship("Task", back_populates="animal", cascade="all, delete-orphan")