from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ComplaintCreate(BaseModel):
    target_type: str
    target_id: int
    reason_category: str
    reason_comment: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: int
    complainant_id: int
    target_type: str
    target_id: int
    reason_category: str
    reason_comment: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True