from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Breed(Base):
    __tablename__ = "breeds"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("animal_species.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description_short = Column(Text, nullable=True)
    card = relationship("BreedCard", uselist=False, back_populates="breed")
    species = relationship("AnimalSpecies", back_populates="breeds")


class BreedCard(Base):
    __tablename__ = "breed_cards"

    breed_id = Column(Integer, ForeignKey("breeds.id"), primary_key=True)
    description = Column(Text, nullable=True)
    common_diseases = Column(Text, nullable=True)
    feeding_tips = Column(Text, nullable=True)
    socialization_tips = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)

    breed = relationship("Breed", back_populates="card")