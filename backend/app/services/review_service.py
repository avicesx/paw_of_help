from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Review, Task, TaskResponse
from app.schemas.reviews import ReviewCreateRequest, ReviewTargetType


async def create_review(reviewer_id: int, payload: ReviewCreateRequest, db: AsyncSession) -> Review:
    if payload.reviewee_id == reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя оставить отзыв самому себе",
        )

    if payload.target_type == "task":
        task = await db.get(Task, payload.target_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        if task.status != "done":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Отзыв можно оставить только по завершённой задаче",
            )

        accepted_volunteers = list(
            (
                await db.scalars(
                    select(TaskResponse.volunteer_id).where(
                        TaskResponse.task_id == task.id,
                        TaskResponse.status == "accepted",
                    )
                )
            ).all()
        )

        if reviewer_id == task.created_by:
            if payload.reviewee_id not in accepted_volunteers:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Отзыв по задаче можно оставить только волонтёру, который выполнял задачу",
                )
        elif reviewer_id in accepted_volunteers:
            if payload.reviewee_id != task.created_by:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Волонтёр может оставить отзыв по задаче только владельцу/организации (создателю задачи)",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Отзыв по задаче могут оставлять только участники задачи",
            )

    existing = await db.scalar(
        select(Review).where(
            Review.reviewer_id == reviewer_id,
            Review.target_type == payload.target_type,
            Review.target_id == payload.target_id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вы уже оставляли отзыв для этой сущности",
        )

    review = Review(
        reviewer_id=reviewer_id,
        reviewee_id=payload.reviewee_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def list_reviews(target_type: ReviewTargetType, target_id: int, db: AsyncSession) -> list[Review]:
    q = select(Review).where(
        Review.target_type == target_type,
        Review.target_id == target_id,
    ).order_by(Review.created_at.desc())
    return list((await db.scalars(q)).all())