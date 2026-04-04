from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.sql import func
from app.core.database import Base


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"
 
    user_id = Column(Integer, primary_key=True)
    location = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True, index=True)
    location_lng = Column(Float, nullable=True, index=True)
    radius_km = Column(Integer, nullable=True)
    availability = Column(JSON, default=lambda: {})
    preferred_animal_types = Column(JSON, default=lambda: [])
    ready_for_foster = Column(Boolean, default=False)
    housing_type = Column(String(50), nullable=True)
    has_other_pets = Column(JSON, default=lambda: {})
    has_children = Column(Boolean, default=False)
    foster_restrictions = Column(Text, nullable=True)
    foster_photos = Column(JSON, default=lambda: [])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Skill(Base):
    __tablename__ = "skills"
 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
 
 
class VolunteerSkill(Base):
    __tablename__ = "volunteer_skills"
 
    user_id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, primary_key=True)
    level = Column(String(50), nullable=True)