from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.misc import SupportTicket
from app.schemas.support_ticket import SupportTicketCreate
from fastapi import HTTPException, status


async def create_support_ticket(
    db: AsyncSession, ticket_data: SupportTicketCreate, user_id: int
) -> SupportTicket:
    ticket = SupportTicket(
        user_id=user_id,
        subject=ticket_data.subject,
        body=ticket_data.body,
        related_entity_type=ticket_data.related_entity_type,
        related_entity_id=ticket_data.related_entity_id,
        status="new",
        priority="normal"
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_tickets_for_user(
    db: AsyncSession, user_id: int
) -> list[SupportTicket]:
    result = await db.scalars(
        select(SupportTicket)
        .where(SupportTicket.user_id == user_id)
        .order_by(SupportTicket.created_at.desc())
    )
    return result.all()