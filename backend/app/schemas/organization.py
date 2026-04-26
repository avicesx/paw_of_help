from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    """Заявка на создание организации"""

    name: str
    description: Optional[str] = None
    inn: Optional[str] = None
    address: Optional[str] = None
    address_lat: Optional[float] = None
    address_lng: Optional[float] = None
    address_components: Dict[str, Any] = {}
    contacts: Dict[str, Any] = {}
    documents: List[str] = []
    logo_url: Optional[str] = None
    photos: List[str] = []


class OrganizationUpdate(BaseModel):
    """Поля профиля организации для сотрудников"""

    name: Optional[str] = None
    description: Optional[str] = None
    inn: Optional[str] = None
    address: Optional[str] = None
    address_lat: Optional[float] = None
    address_lng: Optional[float] = None
    address_components: Optional[Dict[str, Any]] = None
    contacts: Optional[Dict[str, Any]] = None
    documents: Optional[List[str]] = None
    logo_url: Optional[str] = None
    photos: Optional[List[str]] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    inn: Optional[str] = None
    address: Optional[str] = None
    address_lat: Optional[float] = None
    address_lng: Optional[float] = None
    address_components: Dict[str, Any] = {}
    contacts: Dict[str, Any] = {}
    logo_url: Optional[str] = None
    photos: List[str] = []
    status: str
    created_by: int
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationUserResponse(BaseModel):
    organization_id: int
    user_id: int
    role: str
    invitation_status: str
    invited_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InviteUserRequest(BaseModel):
    username: str = Field(..., description="логин пользователя")
    role: str = "curator"


class OrganizationUserRoleUpdate(BaseModel):
    """Смена роли сотрудника организации (только админ)"""

    role: str = Field(..., description="admin|curator")