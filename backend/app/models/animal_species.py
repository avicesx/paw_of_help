from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class AnimalSpecies(Base):
    __tablename__ = "animal_species"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

