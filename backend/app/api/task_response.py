from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models.user import User
from app.schemas.task import TaskResponseCreate, TaskResponseResponse
from app.services.task_response import (
    create_task_response,
    get_task_responses_for_curator,
    update_task_response_status,
)

router = APIRouter(prefix="/task-responses", tags=["task responses"])

@router.post("/{task_id}", response_model=TaskResponseResponse, status_code=status.HTTP_201_CREATED)
async def submit_response(
    task_id: int,
    payload: TaskResponseCreate,
    volunteer: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Волонтёр подаёт отклик на задачу."""
    response = await create_task_response(db, payload, task_id, volunteer)
    return TaskResponseResponse.model_validate(response)

@router.get("/task/{task_id}", response_model=list[TaskResponseResponse])
async def list_responses_for_task(
    task_id: int,
    curator: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Куратор просматривает все отклики на задачу."""
    responses = await get_task_responses_for_curator(db, task_id, curator)
    return [TaskResponseResponse.model_validate(r) for r in responses]

@router.patch("/{response_id}", response_model=TaskResponseResponse)
async def update_response_status(
    response_id: int,
    payload: TaskResponseUpdate,
    curator: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    response = await update_task_response_status(db, response_id, payload.status, curator)
    return TaskResponseResponse.model_validate(response)