from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class OrganizationCreate(BaseModel):
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
    login: str
    role: str = "curator"