from sqlalchemy import Column, Date, DateTime, Enum, Float, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    animal_id = Column(
        Integer,
        ForeignKey("animals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(100), nullable=True)
    urgency = Column(
        Enum("normal", "urgent", name="task_urgency"),
        nullable=False,
        default="normal",
    )
    location = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True, index=True)
    location_lng = Column(Float, nullable=True, index=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    scheduled_time = Column(JSON, nullable=True)
    status = Column(
        Enum("open", "on_review", "in_progress", "done", "cancelled", name="task_status"),
        nullable=False,
        default="open",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    animal = relationship("Animal", back_populates="tasks")
    responses = relationship("TaskResponse", back_populates="task", cascade="all, delete-orphan")
    completion_reports = relationship("TaskCompletionReport", back_populates="task")


class TaskResponse(Base):
    __tablename__ = "task_responses"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    volunteer_id = Column(Integer, nullable=False, index=True)
    status = Column(
        Enum("pending", "accepted", "declined", name="task_response_status"),
        nullable=False,
        default="pending",
    )
    message = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    task = relationship("Task", back_populates="responses")
    volunteer = relationship("User", foreign_keys=[volunteer_id])


class TaskCompletionReport(Base):
    __tablename__ = "task_completion_reports"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    volunteer_id = Column(Integer, nullable=False, index=True)
    status = Column(
        Enum("submitted", "approved", "rejected", name="task_completion_status"),
        nullable=False,
        default="submitted",
    )
    hours_spent = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    photos = Column(JSON, default=lambda: [])
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="completion_reports")
    volunteer = relationship("User", foreign_keys=[volunteer_id])