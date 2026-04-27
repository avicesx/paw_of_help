from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.misc import Report
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

    report = Report(
        reporter_id=reporter_id,
        target_type=report_data.target_type,
        target_id=report_data.target_id,
        reason=report_data.reason,
        description=report_data.description,
        status="pending"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report