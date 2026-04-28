from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.misc import Report, ReportReason
from app.schemas.report import ReportCreate
from fastapi import HTTPException, status


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

    rr = await db.scalar(
        select(ReportReason).where(
            ReportReason.target_type == report_data.target_type,
            ReportReason.code == report_data.reason_code,
            ReportReason.is_active.is_(True),
        )
    )
    if rr is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неизвестная причина жалобы",
        )

    report = Report(
        reporter_id=reporter_id,
        target_type=report_data.target_type,
        target_id=report_data.target_id,
        reason_code=report_data.reason_code,
        reason=rr.title,
        description=report_data.description,
        status="pending",
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report