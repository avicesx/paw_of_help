from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_service import create_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    payload: ReportCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Отправить жалобу на отзыв, статью, сообщение, пользователя или организацию."""
    report = await create_report(db, payload, current_user.id)
    return ReportResponse.model_validate(report)