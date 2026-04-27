from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models.user import User
from app.schemas.support_ticket import SupportTicketCreate, SupportTicketListResponse
from app.services.support_ticket_service import create_support_ticket, get_tickets_for_user

router = APIRouter(prefix="/support-tickets", tags=["support-tickets"])


@router.post("/", response_model=SupportTicketListResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: SupportTicketCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Создать тикет поддержки."""
    ticket = await create_support_ticket(db, payload, current_user.id)
    return SupportTicketListResponse.model_validate(ticket)


@router.get("/", response_model=List[SupportTicketListResponse])
async def list_my_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Получить список своих тикетов."""
    tickets = await get_tickets_for_user(db, current_user.id)
    return [SupportTicketListResponse.model_validate(t) for t in tickets]