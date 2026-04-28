from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models.user import User
from app.models import ReportReason
from app.schemas.report import ReportCreate, ReportResponse, ReportReasonResponse, ReportReasonTargetType
from app.services.report_service import create_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/reasons",
    response_model=list[ReportReasonResponse],
    summary="Справочник причин жалоб",
)
async def list_report_reasons(
    target_type: ReportReasonTargetType,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(ReportReason)
        .where(ReportReason.target_type == target_type, ReportReason.is_active.is_(True))
        .order_by(ReportReason.sort_order.asc(), ReportReason.id.asc())
    )
    rows = (await db.scalars(q)).all()
    return [ReportReasonResponse.model_validate(r) for r in rows]


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    payload: ReportCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Отправить жалобу на отзыв, статью, сообщение, пользователя или организацию."""
    report = await create_report(db, payload, current_user.id)
    return ReportResponse.model_validate(report)