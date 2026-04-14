from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, exists, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import (
    Chat,
    ChatMessage,
    FosterOffer,
    FosterRequest,
    OrganizationUser,
    Task,
    TaskResponse,
    User,
)
from app.schemas.communication import ChatMessageCreate, ChatMessageResponse, ChatResponse


router = APIRouter(prefix="/chats", tags=["chats"])


class OpenChatRequest(BaseModel):
    context_type: str
    context_id: int


class HasUnreadResponse(BaseModel):
    has_unread: bool


async def _get_chat_or_404(db: AsyncSession, chat_id: int) -> Chat:
    chat = await db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat


async def _can_access_context(
    db: AsyncSession, *, context_type: str, context_id: int, user_id: int
) -> bool:
    """
    проверка:
    - task: сотрудник организации или волонтёр, который откликался на задачу
    - foster_request: владелец заявки или волонтёр, который делал отклик
    """
    if context_type == "task":
        task = await db.get(Task, context_id)
        if task is None:
            return False
        staff_q = select(exists().where(
            OrganizationUser.organization_id == task.organization_id,
            OrganizationUser.user_id == user_id,
            OrganizationUser.invitation_status == "accepted",
        ))
        is_staff = await db.scalar(staff_q)
        if is_staff:
            return True
        resp_q = select(exists().where(
            TaskResponse.task_id == task.id,
            TaskResponse.volunteer_id == user_id,
        ))
        return bool(await db.scalar(resp_q))

    if context_type == "foster_request":
        fr = await db.get(FosterRequest, context_id)
        if fr is None:
            return False
        if fr.owner_id == user_id:
            return True
        offer_q = select(exists().where(
            FosterOffer.foster_request_id == fr.id,
            FosterOffer.volunteer_id == user_id,
        ))
        return bool(await db.scalar(offer_q))

    # support_ticket пока не реализуем в MVP
    return False


@router.get(
    "",
    response_model=list[ChatResponse],
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def list_my_chats(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    список чатов, доступных текущему пользователю
    """
    chats = (await db.scalars(select(Chat).order_by(Chat.updated_at.desc().nullslast(), Chat.id.desc()))).all()
    visible: list[ChatResponse] = []
    for c in chats:
        if await _can_access_context(db, context_type=c.context_type, context_id=c.context_id, user_id=current.id):
            visible.append(ChatResponse.model_validate(c))
    return visible


@router.get(
    "/has-unread",
    response_model=HasUnreadResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def has_unread(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """есть ли хотя бы одно непрочитанное сообщение в яатах"""
    chats = (await db.scalars(select(Chat).order_by(Chat.id.desc()))).all()
    for c in chats:
        if not await _can_access_context(
            db, context_type=c.context_type, context_id=c.context_id, user_id=current.id
        ):
            continue
        unread_q = select(
            exists().where(
                ChatMessage.chat_id == c.id,
                ChatMessage.sender_id != current.id,
                ChatMessage.is_read.is_(False),
            )
        )
        if await db.scalar(unread_q):
            return HasUnreadResponse(has_unread=True)
    return HasUnreadResponse(has_unread=False)


@router.post(
    "/open",
    response_model=ChatResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def open_chat(
    payload: OpenChatRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """открыть или создать чат для контекста"""
    if payload.context_type not in {"task", "foster_request"}:
        raise HTTPException(status_code=400, detail="Неподдерживаемый context_type")

    allowed = await _can_access_context(
        db, context_type=payload.context_type, context_id=payload.context_id, user_id=current.id
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    existing = await db.scalar(
        select(Chat).where(
            Chat.context_type == payload.context_type,
            Chat.context_id == payload.context_id,
        )
    )
    if existing:
        return ChatResponse.model_validate(existing)

    chat = Chat(context_type=payload.context_type, context_id=payload.context_id)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return ChatResponse.model_validate(chat)


@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def get_chat(
    chat_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    chat = await _get_chat_or_404(db, chat_id)
    if not await _can_access_context(db, context_type=chat.context_type, context_id=chat.context_id, user_id=current.id):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return ChatResponse.model_validate(chat)


@router.get(
    "/{chat_id}/messages",
    response_model=list[ChatMessageResponse],
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def list_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    chat = await _get_chat_or_404(db, chat_id)
    if not await _can_access_context(db, context_type=chat.context_type, context_id=chat.context_id, user_id=current.id):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    q = (
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.scalars(q)).all()
    rows = list(reversed(rows))
    return [ChatMessageResponse.model_validate(r) for r in rows]


@router.post(
    "/{chat_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def send_message(
    chat_id: int,
    payload: ChatMessageCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    chat = await _get_chat_or_404(db, chat_id)
    if not await _can_access_context(db, context_type=chat.context_type, context_id=chat.context_id, user_id=current.id):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    msg = ChatMessage(
        chat_id=chat_id,
        sender_id=current.id,
        message_type=payload.message_type,
        content=payload.content,
        is_read=False,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return ChatMessageResponse.model_validate(msg)


@router.post(
    "/{chat_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def mark_chat_read(
    chat_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Отметить все чужие сообщения в чате как прочитанные"""
    chat = await _get_chat_or_404(db, chat_id)
    if not await _can_access_context(db, context_type=chat.context_type, context_id=chat.context_id, user_id=current.id):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    await db.execute(
        update(ChatMessage)
        .where(
            ChatMessage.chat_id == chat_id,
            ChatMessage.sender_id != current.id,
            ChatMessage.is_read.is_(False),
        )
        .values(is_read=True)
    )
    await db.commit()
    return None