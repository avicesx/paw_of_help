from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintCreate
from fastapi import HTTPException, status


async def create_complaint(
    db: AsyncSession, complaint_data: ComplaintCreate, user_id: int
) -> Complaint:
    existing = await db.execute(
        select(Complaint).where(
            Complaint.complainant_id == user_id,
            Complaint.target_type == complaint_data.target_type,
            Complaint.target_id == complaint_data.target_id
        )
    )
    existing_complaint = existing.scalars().first()

    if existing_complaint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже отправляли жалобу на этот контент."
        )

    complaint = Complaint(
        complainant_id=user_id,
        target_type=complaint_data.target_type,
        target_id=complaint_data.target_id,
        reason_category=complaint_data.reason_category,
        reason_comment=complaint_data.reason_comment,
        status="pending"
    )

    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return complaint