from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models.user import User
from app.schemas.complaint import ComplaintCreate, ComplaintResponse
from app.services.complaint_service import create_complaint

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def submit_complaint(
    payload: ComplaintCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Отправить жалобу на отзыв, статью, сообщение, пользователя или организацию."""
    complaint = await create_complaint(db, payload, current_user.id)
    return ComplaintResponse.model_validate(complaint)