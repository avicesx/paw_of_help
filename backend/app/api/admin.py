from datetime import datetime, timedelta
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models import (
    AuditLog,
    BlogComment,
    KnowledgeBaseArticle,
    Organization,
    Report,
    Review,
    SupportTicket,
    SupportTicketMessage,
    Task,
    User,
    Post,
)
from app.schemas.admin import (
    AuditLogItem,
    ContentReviewItem,
    OrganizationListItem,
    OrganizationRejectRequest,
    ReportListItem,
    RejectContentRequest,
    RoleUpdateRequest,
    SupportTicketDetail,
    SupportTicketListItem,
    SupportTicketReplyRequest,
    SupportTicketStatusUpdateRequest,
    UserListItem,
)
from app.services import create_notification


router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin_access(current_user: User) -> None:
    """Доступ к админке: admin, moderator, support_agent, superadmin."""
    if current_user.role not in {"admin", "moderator", "support_agent", "superadmin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")


def _require_moderation_access(current_user: User) -> None:
    """Доступ к контент-ревью и репортам: admin, moderator, superadmin."""
    if current_user.role not in {"admin", "moderator", "superadmin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")


def _require_support_access(current_user: User) -> None:
    """Доступ к поддержке: admin, support_agent, superadmin."""
    if current_user.role not in {"admin", "support_agent", "superadmin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")


def _require_user_management_access(current_user: User) -> None:
    """Доступ к управлению пользователями/организациями: admin, superadmin."""
    if current_user.role not in {"admin", "superadmin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")


def _require_superadmin_only(current_user: User) -> None:
    """Только для суперадмина."""
    if current_user.role != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуется суперадмин")


async def _get_user_or_404(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


async def _get_org_or_404(db: AsyncSession, organization_id: int) -> Organization:
    org = await db.get(Organization, organization_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Организация не найдена")
    return org


async def _get_ticket_or_404(db: AsyncSession, ticket_id: int) -> SupportTicket:
    ticket = await db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тикет не найден")
    return ticket


def _format_full_name(user: Optional[User]) -> Optional[str]:
    if not user:
        return None
    parts = [part for part in [user.name, user.last_name] if part]
    return " ".join(parts) if parts else user.username


async def _log_action(
    db: AsyncSession,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
        )
    )


async def _hide_user_content(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(Task).where(Task.created_by == user_id).values(is_hidden=True)
    )
    await db.execute(
        update(Post).where(Post.author_user_id == user_id).values(is_hidden=True)
    )
    await db.execute(
        update(BlogComment).where(BlogComment.user_id == user_id).values(is_hidden=True)
    )
    await db.execute(
        update(Review).where(Review.reviewer_id == user_id).values(is_hidden=True)
    )


async def _unhide_user_content(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(Task).where(Task.created_by == user_id).values(is_hidden=False)
    )
    await db.execute(
        update(Post).where(Post.author_user_id == user_id).values(is_hidden=False)
    )
    await db.execute(
        update(BlogComment).where(BlogComment.user_id == user_id).values(is_hidden=False)
    )
    await db.execute(
        update(Review).where(Review.reviewer_id == user_id).values(is_hidden=False)
    )


@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin_access(current_user)
    week_ago = datetime.utcnow() - timedelta(days=7)

    total_users = await db.scalar(select(func.count()).select_from(User))
    users_new_week = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= week_ago)
    )
    total_organizations_verified = await db.scalar(
        select(func.count()).select_from(Organization).where(Organization.status == "active")
    )
    active_tasks = await db.scalar(
        select(func.count()).select_from(Task).where(Task.status == "open")
    )
    total_posts = await db.scalar(select(func.count()).select_from(Post))
    open_tickets = await db.scalar(
        select(func.count()).select_from(SupportTicket).where(SupportTicket.status != "closed")
    )
    pending_reports = await db.scalar(
        select(func.count()).select_from(Report).where(Report.status == "pending")
    )

    return {
        "total_users": int(total_users or 0),
        "users_new_week": int(users_new_week or 0),
        "total_organizations_verified": int(total_organizations_verified or 0),
        "active_tasks": int(active_tasks or 0),
        "total_posts": int(total_posts or 0),
        "open_tickets": int(open_tickets or 0),
        "pending_reports": int(pending_reports or 0),
    }


@router.get("/users", response_model=list[UserListItem])
async def list_users(
    status: Optional[Literal["active", "blocked"]] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin_access(current_user)

    completed_tasks_subquery = (
        select(func.count(Task.id))
        .where(Task.created_by == User.id, Task.status == "done")
        .scalar_subquery()
    )
    rating_subquery = (
        select(func.avg(Review.rating))
        .where(Review.reviewee_id == User.id)
        .scalar_subquery()
    )

    stmt = select(
        User,
        completed_tasks_subquery.label("completed_tasks"),
        rating_subquery.label("rating"),
    )

    if status == "active":
        stmt = stmt.where(User.is_active.is_(True))
    elif status == "blocked":
        stmt = stmt.where(User.is_active.is_(False))

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.phone.ilike(pattern),
                User.name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
        )

    stmt = stmt.order_by(User.created_at.desc())
    rows = (await db.execute(stmt)).all()

    users = []
    for user, completed_tasks, rating in rows:
        users.append(
            UserListItem(
                id=user.id,
                name=user.name,
                last_name=user.last_name,
                username=user.username,
                email=user.email,
                phone=user.phone,
                is_active=user.is_active,
                created_at=user.created_at,
                completed_tasks=int(completed_tasks or 0),
                rating=float(rating or 0.0),
            )
        )
    return users


@router.patch("/users/{user_id}/block")
async def block_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_user_management_access(current_user)
    user = await _get_user_or_404(db, user_id)
    before = {"is_active": user.is_active}
    user.is_active = False
    await _hide_user_content(db, user.id)
    await _log_action(
        db,
        actor_id=current_user.id,
        action="block_user",
        entity_type="user",
        entity_id=user.id,
        before_state=before,
        after_state={"is_active": user.is_active},
    )
    await create_notification(
        db,
        user_id=user.id,
        type="account_blocked",
        title="Ваш аккаунт заблокирован",
        body="Ваш аккаунт был заблокирован администрацией.",
        commit=False,
    )
    await db.commit()
    return {"detail": "Пользователь заблокирован"}


@router.patch("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_user_management_access(current_user)
    user = await _get_user_or_404(db, user_id)
    before = {"is_active": user.is_active}
    user.is_active = True
    await _unhide_user_content(db, user.id)
    await _log_action(
        db,
        actor_id=current_user.id,
        action="unblock_user",
        entity_type="user",
        entity_id=user.id,
        before_state=before,
        after_state={"is_active": user.is_active},
    )
    await create_notification(
        db,
        user_id=user.id,
        type="account_unblocked",
        title="Ваш аккаунт восстановлен",
        body="Ваш аккаунт был разблокирован администрацией.",
        commit=False,
    )
    await db.commit()
    return {"detail": "Пользователь разблокирован"}


@router.patch("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_superadmin_only(current_user)
    user = await _get_user_or_404(db, user_id)
    before = {"role": user.role}
    user.role = payload.role
    await _log_action(
        db,
        actor_id=current_user.id,
        action="change_user_role",
        entity_type="user",
        entity_id=user.id,
        before_state=before,
        after_state={"role": user.role},
    )
    await create_notification(
        db,
        user_id=user.id,
        type="role_changed",
        title="Роль пользователя обновлена",
        body=f"Ваша роль была изменена на {user.role}.",
        commit=False,
    )
    await db.commit()
    return {"detail": "Роль пользователя обновлена"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_superadmin_only(current_user)
    user = await _get_user_or_404(db, user_id)
    await _log_action(
        db,
        actor_id=current_user.id,
        action="delete_user",
        entity_type="user",
        entity_id=user.id,
        before_state={"id": user.id, "username": user.username, "email": user.email},
        after_state=None,
    )
    await db.execute(delete(Review).where(or_(Review.reviewer_id == user.id, Review.reviewee_id == user.id)))
    await db.execute(delete(SupportTicketMessage).where(SupportTicketMessage.sender_id == user.id))
    await db.execute(delete(SupportTicket).where(SupportTicket.user_id == user.id))
    await db.execute(delete(Report).where(or_(Report.reporter_id == user.id, Report.moderator_id == user.id)))
    await db.execute(delete(Post).where(Post.author_user_id == user.id))
    await db.execute(delete(BlogComment).where(BlogComment.user_id == user.id))
    await db.execute(delete(Task).where(Task.created_by == user.id))
    await db.delete(user)
    await db.commit()
    return {"detail": "Пользователь и связанные данные удалены"}


@router.get("/organizations", response_model=list[OrganizationListItem])
async def list_organizations(
    status: Optional[Literal["pending", "active", "blocked"]] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin_access(current_user)

    stmt = select(Organization)
    if status:
        stmt = stmt.where(Organization.status == status)
    if search:
        stmt = stmt.where(Organization.name.ilike(f"%{search.strip()}%"))
    stmt = stmt.order_by(Organization.created_at.desc())
    organizations = (await db.scalars(stmt)).all()

    rows = []
    for org in organizations:
        creator = await db.get(User, org.created_by)
        rows.append(
            OrganizationListItem(
                id=org.id,
                name=org.name,
                status=org.status,
                created_at=org.created_at,
                contact_person=_format_full_name(creator),
            )
        )
    return rows


@router.patch("/organizations/{organization_id}/verify")
async def verify_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_user_management_access(current_user)
    org = await _get_org_or_404(db, organization_id)
    before = {"status": org.status}
    org.status = "active"
    org.rejection_reason = None
    await _log_action(
        db,
        actor_id=current_user.id,
        action="verify_organization",
        entity_type="organization",
        entity_id=org.id,
        before_state=before,
        after_state={"status": org.status},
    )
    await create_notification(
        db,
        user_id=org.created_by,
        type="organization_verified",
        title="Организация подтверждена",
        body=f"Организация \"{org.name}\" прошла верификацию.",
        commit=False,
    )
    await db.commit()
    return {"detail": "Организация подтверждена"}


@router.post("/organizations/{organization_id}/reject")
async def reject_organization(
    organization_id: int,
    payload: OrganizationRejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_user_management_access(current_user)
    org = await _get_org_or_404(db, organization_id)
    before = {"status": org.status, "rejection_reason": org.rejection_reason}
    org.status = "blocked"
    org.rejection_reason = payload.reason
    await _log_action(
        db,
        actor_id=current_user.id,
        action="reject_organization",
        entity_type="organization",
        entity_id=org.id,
        before_state=before,
        after_state={"status": org.status, "rejection_reason": org.rejection_reason},
    )
    await create_notification(
        db,
        user_id=org.created_by,
        type="organization_rejected",
        title="Организация отклонена",
        body=f"Организация \"{org.name}\" отклонена: {payload.reason}",
        commit=False,
    )
    await db.commit()
    return {"detail": "Организация отклонена"}


@router.patch("/organizations/{organization_id}/block")
async def block_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_user_management_access(current_user)
    org = await _get_org_or_404(db, organization_id)
    before = {"status": org.status}
    org.status = "blocked"
    await db.execute(update(Task).where(Task.organization_id == organization_id).values(is_hidden=True))
    await db.execute(update(Post).where(Post.organization_id == organization_id).values(is_hidden=True))
    await _log_action(
        db,
        actor_id=current_user.id,
        action="block_organization",
        entity_type="organization",
        entity_id=org.id,
        before_state=before,
        after_state={"status": org.status},
    )
    await db.commit()
    return {"detail": "Организация заблокирована"}


@router.get("/support-tickets", response_model=list[SupportTicketListItem])
async def list_support_tickets(
    status: Optional[Literal["new", "in_progress", "closed"]] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_support_access(current_user)
    stmt = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status:
        stmt = stmt.where(SupportTicket.status == status)
    ticket_rows = (await db.scalars(stmt)).all()
    tickets = []
    for ticket in ticket_rows:
        reporter = await db.get(User, ticket.user_id)
        if search:
            term = search.strip().lower()
            if term not in str(ticket.id).lower() and term not in (ticket.subject or "").lower() and term not in (reporter.username or "").lower():
                continue
        tickets.append(
            SupportTicketListItem(
                id=ticket.id,
                subject=ticket.subject,
                user_id=ticket.user_id,
                user_name=_format_full_name(reporter),
                status=ticket.status,
                created_at=ticket.created_at,
            )
        )
    return tickets


@router.get("/support-tickets/{ticket_id}", response_model=SupportTicketDetail)
async def get_support_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_support_access(current_user)
    ticket = await _get_ticket_or_404(db, ticket_id)
    reporter = await db.get(User, ticket.user_id)
    messages = (
        await db.scalars(
            select(SupportTicketMessage)
            .where(SupportTicketMessage.ticket_id == ticket.id)
            .order_by(SupportTicketMessage.created_at.asc())
        )
    ).all()
    return SupportTicketDetail(
        id=ticket.id,
        subject=ticket.subject,
        body=ticket.body,
        status=ticket.status,
        priority=ticket.priority,
        user_id=ticket.user_id,
        user_name=_format_full_name(reporter),
        created_at=ticket.created_at,
        messages=[
            SupportTicketMessageItem(
                sender_id=m.sender_id,
                body=m.body,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.post("/support-tickets/{ticket_id}/reply")
async def reply_support_ticket(
    ticket_id: int,
    payload: SupportTicketReplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_support_access(current_user)
    ticket = await _get_ticket_or_404(db, ticket_id)
    message = SupportTicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        body=payload.message,
        is_staff=True,
    )
    ticket.status = "in_progress"
    db.add(message)
    await _log_action(
        db,
        actor_id=current_user.id,
        action="reply_support_ticket",
        entity_type="support_ticket",
        entity_id=ticket.id,
        before_state={"status": ticket.status},
        after_state={"status": ticket.status},
    )
    await create_notification(
        db,
        user_id=ticket.user_id,
        type="support_ticket_reply",
        title="Ответ администратора",
        body=f"Вам ответили в тикете \"{ticket.subject}\".",
        commit=False,
    )
    await db.commit()
    return {"detail": "Ответ добавлен"}


@router.patch("/support-tickets/{ticket_id}/status")
async def update_support_ticket_status(
    ticket_id: int,
    payload: SupportTicketStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_support_access(current_user)
    ticket = await _get_ticket_or_404(db, ticket_id)
    before = {"status": ticket.status}
    ticket.status = payload.status
    await create_notification(
        db,
        user_id=ticket.user_id,
        type="support_ticket_status",
        title="Статус тикета обновлён",
        body=f"Статус вашего тикета \"{ticket.subject}\" изменён на {ticket.status}.",
        commit=False,
    )
    await _log_action(
        db,
        actor_id=current_user.id,
        action="update_support_ticket_status",
        entity_type="support_ticket",
        entity_id=ticket.id,
        before_state=before,
        after_state={"status": ticket.status},
    )
    await db.commit()
    return {"detail": "Статус тикета обновлён"}


async def _fetch_content_author(db: AsyncSession, content_type: str, content_id: int) -> tuple[Optional[User], Optional[object]]:
    if content_type == "post":
        content = await db.get(Post, content_id)
        author_id = content.author_user_id if content else None
    elif content_type == "comment":
        content = await db.get(BlogComment, content_id)
        author_id = content.user_id if content else None
    elif content_type == "article":
        content = await db.get(KnowledgeBaseArticle, content_id)
        author_id = content.author_id if content else None
    elif content_type == "review":
        content = await db.get(Review, content_id)
        author_id = content.reviewer_id if content else None
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип контента")

    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден")

    author = await db.get(User, author_id) if author_id else None
    return author, content


def _content_is_pending(content_type: str, content: object) -> bool:
    if content_type == "article":
        return getattr(content, "status", None) == "on_moderation"
    return getattr(content, "moderation_status", None) in {"pending", "requires_review"}


def _content_preview(content_type: str, content: object) -> str:
    if content_type == "post":
        return (content.content or "")[:200]
    if content_type == "comment":
        return (content.content or "")[:200]
    if content_type == "article":
        return (content.content or "")[:200]
    if content_type == "review":
        return (content.comment or "")[:200]
    return ""


@router.get("/content-review", response_model=list[ContentReviewItem])
async def list_content_review(
    content_type: Literal["post", "comment", "article", "review"],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_moderation_access(current_user)

    items = []
    if content_type == "post":
        rows = (await db.scalars(select(Post).where(Post.moderation_status.in_(["pending", "requires_review"])))).all()
    elif content_type == "comment":
        rows = (await db.scalars(select(BlogComment).where(BlogComment.moderation_status.in_(["pending", "requires_review"])))).all()
    elif content_type == "article":
        rows = (await db.scalars(select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.status == "on_moderation"))).all()
    elif content_type == "review":
        rows = (await db.scalars(select(Review).where(Review.moderation_status.in_(["pending", "requires_review"])))).all()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип контента")

    for content in rows:
        author = None
        if content_type == "post":
            author = await db.get(User, content.author_user_id)
        elif content_type == "comment":
            author = await db.get(User, content.user_id)
        elif content_type == "article":
            author = await db.get(User, content.author_id)
        elif content_type == "review":
            author = await db.get(User, content.reviewer_id)

        items.append(
            ContentReviewItem(
                id=content.id,
                type=content_type,
                author_name=_format_full_name(author),
                content=_content_preview(content_type, content),
                reason=getattr(content, "moderation_reason", None) or getattr(content, "rejection_reason", None),
                created_at=content.created_at,
            )
        )
    return items


async def _perform_content_review_action(
    db: AsyncSession,
    content_type: str,
    content_id: int,
    new_status: str,
    reason: Optional[str],
) -> tuple[Optional[int], Optional[int], dict, dict]:
    if content_type == "post":
        content = await db.get(Post, content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден")
        before = {"moderation_status": content.moderation_status, "is_hidden": content.is_hidden}
        content.moderation_status = new_status
        content.is_hidden = new_status != "approved"
        content.moderation_reason = reason
        after = {"moderation_status": content.moderation_status, "is_hidden": content.is_hidden}
        author_id = content.author_user_id
        entity_type = "post"
    elif content_type == "comment":
        content = await db.get(BlogComment, content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден")
        before = {"moderation_status": content.moderation_status, "is_hidden": content.is_hidden}
        content.moderation_status = new_status
        content.is_hidden = new_status != "approved"
        content.moderation_reason = reason
        after = {"moderation_status": content.moderation_status, "is_hidden": content.is_hidden}
        author_id = content.user_id
        entity_type = "comment"
    elif content_type == "article":
        content = await db.get(KnowledgeBaseArticle, content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден")
        before = {"status": content.status, "published": content.published}
        if new_status == "approved":
            content.status = "published"
            content.published = True
            content.rejection_reason = None
        else:
            content.status = "rejected"
            content.published = False
            content.rejection_reason = reason
        after = {"status": content.status, "published": content.published}
        author_id = content.author_id
        entity_type = "article"
    elif content_type == "review":
        content = await db.get(Review, content_id)
        if content is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден")
        before = {"moderation_status": content.moderation_status, "is_hidden": content.is_hidden}
        content.moderation_status = new_status
        content.is_hidden = new_status != "approved"
        content.moderation_reason = reason
        after = {"moderation_status": content.moderation_status, "is_hidden": content.is_hidden}
        author_id = content.reviewer_id
        entity_type = "review"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип контента")

    return author_id, entity_type, before, after


@router.post("/content-review/{content_type}/{content_id}/approve")
async def approve_content_review(
    content_type: Literal["post", "comment", "article", "review"],
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_moderation_access(current_user)
    author_id, entity_type, before, after = await _perform_content_review_action(
        db, content_type, content_id, "approved", None
    )
    await _log_action(
        db,
        actor_id=current_user.id,
        action="approve_content",
        entity_type=entity_type,
        entity_id=content_id,
        before_state=before,
        after_state=after,
    )
    await db.commit()
    return {"detail": "Контент одобрен"}


@router.post("/content-review/{content_type}/{content_id}/reject")
async def reject_content_review(
    content_type: Literal["post", "comment", "article", "review"],
    content_id: int,
    payload: RejectContentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_moderation_access(current_user)
    author_id, entity_type, before, after = await _perform_content_review_action(
        db, content_type, content_id, "rejected", payload.reason
    )
    if author_id:
        await create_notification(
            db,
            user_id=author_id,
            type="content_rejected",
            title="Контент отклонён модерацией",
            body=f"Ваш контент был отклонён: {payload.reason}",
            commit=False,
        )
    await _log_action(
        db,
        actor_id=current_user.id,
        action="reject_content",
        entity_type=entity_type,
        entity_id=content_id,
        before_state=before,
        after_state=after,
    )
    await db.commit()
    return {"detail": "Контент отклонён"}


@router.post("/content-review/{content_type}/{content_id}/block-author")
async def block_content_author(
    content_type: Literal["post", "comment", "article", "review"],
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_moderation_access(current_user)
    author, content = await _fetch_content_author(db, content_type, content_id)
    if author is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")
    before = {"is_active": author.is_active}
    author.is_active = False
    await _hide_user_content(db, author.id)
    await create_notification(
        db,
        user_id=author.id,
        type="account_blocked",
        title="Ваш аккаунт заблокирован",
        body="Ваш аккаунт был заблокирован за нарушение правил.",
        commit=False,
    )
    await _log_action(
        db,
        actor_id=current_user.id,
        action="block_content_author",
        entity_type=content_type,
        entity_id=content_id,
        before_state=before,
        after_state={"is_active": author.is_active},
    )
    await db.commit()
    return {"detail": "Автор заблокирован"}


@router.get("/reports", response_model=list[ReportListItem])
async def list_reports(
    status: Optional[Literal["pending", "resolved"]] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_moderation_access(current_user)
    stmt = select(Report).order_by(Report.created_at.desc())
    if status:
        stmt = stmt.where(Report.status == status)

    reports = (await db.scalars(stmt)).all()
    items = []
    for report in reports:
        reporter = await db.get(User, report.reporter_id)
        if search:
            term = search.strip().lower()
            if term not in (report.reason or "").lower() and term not in (report.description or "").lower() and term not in (reporter.username or "").lower():
                continue
        items.append(
            ReportListItem(
                id=report.id,
                target_type=report.target_type,
                target_id=report.target_id,
                reason=report.reason,
                comment=report.description,
                reporter_name=_format_full_name(reporter),
                created_at=report.created_at,
            )
        )
    return items


@router.post("/reports/{report_id}/dismiss")
async def dismiss_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_moderation_access(current_user)
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жалоба не найдена")
    before = {"status": report.status}
    report.status = "rejected"
    report.moderator_id = current_user.id
    await _log_action(
        db,
        actor_id=current_user.id,
        action="dismiss_report",
        entity_type="report",
        entity_id=report.id,
        before_state=before,
        after_state={"status": report.status},
    )
    await db.commit()
    return {"detail": "Жалоба отклонена"}


async def _remove_reported_content(
    db: AsyncSession,
    report: Report,
    actor_id: int,
) -> tuple[Optional[int], Optional[str], Optional[str]]:
    target_type = report.target_type
    target_id = report.target_id
    author_id: Optional[int] = None
    content_type = target_type

    if target_type == "post":
        post = await db.get(Post, target_id)
        if post:
            author_id = post.author_user_id
            post.is_hidden = True
            post.moderation_status = "rejected"
            post.moderation_reason = "Удалено по жалобе"
    elif target_type == "comment":
        comment = await db.get(BlogComment, target_id)
        if comment:
            author_id = comment.user_id
            comment.is_hidden = True
            comment.moderation_status = "rejected"
            comment.moderation_reason = "Удалено по жалобе"
    elif target_type == "article":
        article = await db.get(KnowledgeBaseArticle, target_id)
        if article:
            author_id = article.author_id
            article.status = "rejected"
            article.published = False
            article.rejection_reason = "Удалено по жалобе"
    elif target_type == "review":
        review = await db.get(Review, target_id)
        if review:
            author_id = review.reviewer_id
            review.is_hidden = True
            review.moderation_status = "rejected"
            review.moderation_reason = "Удалено по жалобе"
    elif target_type == "task":
        task = await db.get(Task, target_id)
        if task:
            author_id = task.created_by
            task.is_hidden = True
            task.status = "cancelled"
    elif target_type == "user":
        user = await db.get(User, target_id)
        if user:
            author_id = user.id
            user.is_active = False
            await _hide_user_content(db, author_id)
    elif target_type == "organization":
        org = await db.get(Organization, target_id)
        if org:
            author_id = org.created_by
            org.status = "blocked"
            await db.execute(update(Task).where(Task.organization_id == target_id).values(is_hidden=True))
            await db.execute(update(Post).where(Post.organization_id == target_id).values(is_hidden=True))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Тип жалобы не поддерживается")

    if author_id:
        await create_notification(
            db,
            user_id=author_id,
            type="content_removed",
            title="Контент удалён администратором",
            body=f"Ваш контент, на который была подана жалоба, был удалён или скрыт.",
            commit=False,
        )
    await _log_action(
        db,
        actor_id=actor_id,
        action="remove_reported_content",
        entity_type=target_type,
        entity_id=target_id,
        before_state={"report_status": report.status},
        after_state={"report_status": "resolved"},
    )
    report.status = "resolved"
    report.moderator_id = actor_id
    return author_id, target_type


@router.post("/reports/{report_id}/remove-content")
async def remove_report_content(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_moderation_access(current_user)
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Жалоба не найдена")
    await _remove_reported_content(db, report, current_user.id)
    await db.commit()
    return {"detail": "Контент удалён"}


@router.get("/audit-logs", response_model=list[AuditLogItem])
async def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    limit: int = Query(100, gt=0, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_superadmin_only(current_user)
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    stmt = stmt.limit(limit)
    rows = (await db.scalars(stmt)).all()
    return [AuditLogItem.model_validate(r) for r in rows]
