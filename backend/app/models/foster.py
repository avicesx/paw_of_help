from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, Integer, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base


class FosterRequest(Base):
    __tablename__ = "foster_requests"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    animal_id = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    dates_flexible = Column(Boolean, default=False)
    pickup_location = Column(Text, nullable=True)
    pickup_lat = Column(Float, nullable=True, index=True)
    pickup_lng = Column(Float, nullable=True, index=True)
    return_location = Column(Text, nullable=True)
    return_lat = Column(Float, nullable=True, index=True)
    return_lng = Column(Float, nullable=True, index=True)
    owner_provides = Column(JSON, default=lambda: {})
    status = Column(
        Enum("draft", "published", "booked", "closed", "cancelled", name="foster_request_status"),
        nullable=False,
        default="draft",
    )
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FosterOffer(Base):
    __tablename__ = "foster_offers"

    id = Column(Integer, primary_key=True, index=True)
    foster_request_id = Column(Integer, nullable=False, index=True)
    volunteer_id = Column(Integer, nullable=False)
    type = Column(
        Enum("offer", "response", name="foster_offer_type"),
        nullable=False,
        default="response",
    )
    status = Column(
        Enum("pending", "accepted", "declined", name="foster_offer_status"),
        nullable=False,
        default="pending",
    )
    proposed_start_date = Column(Date, nullable=True)
    proposed_end_date = Column(Date, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FosterPlacement(Base):
    __tablename__ = "foster_placements"

    id = Column(Integer, primary_key=True, index=True)
    foster_request_id = Column(Integer, nullable=False)
    volunteer_id = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(
        Enum("active", "completed", "cancelled", name="foster_placement_status"),
        nullable=False,
        default="active",
    )
    report = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())