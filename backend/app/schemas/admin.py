from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel


class UserListItem(BaseModel):
    id: int
    name: Optional[str]
    last_name: Optional[str]
    username: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    completed_tasks: int
    rating: float


class RoleUpdateRequest(BaseModel):
    role: Literal["user", "admin", "moderator", "support_agent", "superadmin"]


class OrganizationListItem(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    contact_person: Optional[str]


class OrganizationRejectRequest(BaseModel):
    reason: str


class SupportTicketListItem(BaseModel):
    id: int
    subject: str
    user_id: int
    user_name: Optional[str]
    status: str
    created_at: datetime


class SupportTicketMessageItem(BaseModel):
    sender_id: int
    body: str
    created_at: datetime


class SupportTicketDetail(BaseModel):
    id: int
    subject: str
    body: str
    status: str
    priority: str
    user_id: int
    user_name: Optional[str]
    created_at: datetime
    messages: list[SupportTicketMessageItem] = []


class SupportTicketReplyRequest(BaseModel):
    message: str


class SupportTicketStatusUpdateRequest(BaseModel):
    status: Literal["in_progress", "closed"]


class ContentReviewItem(BaseModel):
    id: int
    type: Literal["post", "comment", "article", "review"]
    author_name: Optional[str]
    content: Optional[str]
    reason: Optional[str]
    created_at: datetime


class RejectContentRequest(BaseModel):
    reason: str


class ReportListItem(BaseModel):
    id: int
    target_type: str
    target_id: int
    reason: Optional[str]
    comment: Optional[str]
    reporter_name: Optional[str]
    created_at: datetime


class AuditLogItem(BaseModel):
    id: int
    actor_id: int
    action: str
    entity_type: str
    entity_id: int
    before_state: Optional[dict]
    after_state: Optional[dict]
    created_at: datetime
