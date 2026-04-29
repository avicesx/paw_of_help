from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, nullable=False)
    reviewee_id = Column(Integer, nullable=False)
    target_type = Column(
        Enum(
            "volunteer", "organization", "task", "foster_request",
            name="review_target_type",
        ),
        nullable=False,
    )
    target_id = Column(Integer, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, nullable=False)
    target_type = Column(
        Enum(
            "user", "organization", "task", "review", "post", "comment", "article",
            name="report_target_type",
        ),
        nullable=False,
    )
    target_id = Column(Integer, nullable=False)
    reason_code = Column(String(100), nullable=True)
    reason = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="pending")
    moderator_id = Column(Integer, nullable=True)
    moderation_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ReportReason(Base):
    __tablename__ = "report_reasons"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(
        Enum(
            "user",
            "organization",
            "article",
            "post",
            "comment",
            name="report_reason_target_type",
        ),
        nullable=False,
        index=True,
    )
    code = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Sighting(Base):
    __tablename__ = "sightings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    location = Column(Text, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    photos = Column(JSON, default=lambda: [])
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(
        Enum("new", "in_progress", "waiting_reply", "closed",
             name="support_ticket_status"),
        nullable=False,
        default="new",
    )
    priority = Column(
        Enum("low", "normal", "high", "urgent", name="support_ticket_priority"),
        nullable=False,
        default="normal",
    )
    assigned_to = Column(Integer, nullable=True)
    related_entity_type = Column(
        Enum("task", "organization", "user", "post", "foster_request", "review",
             name="support_entity_type"),
        nullable=True,
    )
    related_entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship("User", foreign_keys=[user_id], back_populates="tickets")


class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    is_staff = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=False)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)
    criteria = Column(JSON, nullable=False, default=lambda: {})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    achievement_id = Column(Integer, nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())