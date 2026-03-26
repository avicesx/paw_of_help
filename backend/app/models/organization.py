from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, JSON, String, Text
from sqlalchemy.sql import func
from backend.app.core import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    inn = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    contacts = Column(JSON, default=lambda: {})
    documents = Column(JSON, default=lambda: [])
    logo_url = Column(Text, nullable=True)
    photos = Column(JSON, default=lambda: [])
    status = Column(
        Enum("pending", "active", "blocked", "revision_requested",
             name="organization_status"),
        nullable=False,
        default="pending",
    )
    created_by = Column(Integer, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OrganizationUser(Base):
    __tablename__ = "organization_users"

    organization_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    role = Column(
        Enum("admin", "curator", name="user_organization_role"),
        nullable=False,
    )
    invitation_status = Column(
        Enum("pending", "accepted", "declined", name="invitation_status"),
        nullable=False,
        default="pending",
    )
    invited_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())