from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, JSON, String, Text
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=True)
    start_datetime = Column(DateTime(timezone=True), nullable=True)
    end_datetime = Column(DateTime(timezone=True), nullable=True)
    location = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EventParticipant(Base):
    __tablename__ = "event_participants"

    event_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    status = Column(
        Enum("registered", "attended", "cancelled", name="event_participation_status"),
        nullable=False,
        default="registered",
    )
    registered_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    data = Column(JSON, default=lambda: {})
    is_read = Column(Boolean, default=False)
    is_sent_telegram = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    context_type = Column(
        Enum("task", "foster_request", "support_ticket", name="chat_context_type"),
        nullable=False,
    )
    context_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    sender_id = Column(Integer, nullable=False)
    message_type = Column(String(20), default="text")
    content = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())