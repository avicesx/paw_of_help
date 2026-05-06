from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy import select
from app.models.misc import Report
from app.schemas.report import ReportCreate
from fastapi import HTTPException, status
from app.services.ml_guard import get_moderation_agent

logger = logging.getLogger(__name__)

async def create_report(
    db: AsyncSession,
    report_data: ReportCreate,
    reporter_id: int
) -> Report:
    existing = await db.execute(
        select(Report).where(
            Report.reporter_id == reporter_id,
            Report.target_type == report_data.target_type,
            Report.target_id == report_data.target_id
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже отправляли жалобу на этот контент."
        )

    reason_text = (report_data.reason or "") + " " + (report_data.description or "")

    ml = get_moderation_agent()
    status_ = "pending"
    moderation_comment = None

    if ml:
        try:
            result = ml.evaluate(reason_text)
            if result["verdict"] == "BLOCK":
                status_ = "rejected"
                moderation_comment = f"AI-отклонение: {result.get('details', {}).get('reason', 'Оскорбительный/спамовый контент')}"
            else:
                status_ = "pending"
                moderation_comment = "AI-проверка пройдена: контент соответствует правилам"
        except Exception as e:
            logger.error(f"❌ Ошибка в AI-модерации: {e}", exc_info=True)
            moderation_comment = f"Ошибка модерации: {str(e)[:100]}"

    report = Report(
        reporter_id=reporter_id,
        target_type=report_data.target_type,
        target_id=report_data.target_id,
        reason=report_data.reason,
        description=report_data.description,
        status=status_,
        moderation_comment=moderation_comment,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report