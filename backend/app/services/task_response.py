from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import Task, TaskResponse
from app.models.user import User
from app.models.organization import OrganizationUser
from app.models import Skill, VolunteerSkill
from app.schemas.task import TaskResponseCreate
from app.services import create_notification


async def create_task_response(
    db: AsyncSession,
    payload: TaskResponseCreate,
    task_id: int,
    volunteer: User,
) -> TaskResponse:
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task.status != "open":
        raise HTTPException(status_code=400, detail="Задача больше не доступна для отклика")

    existing = await db.scalar(
        select(TaskResponse).where(
            TaskResponse.task_id == task_id,
            TaskResponse.volunteer_id == volunteer.id,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже откликнулись на эту задачу")

    skill_ids = await db.scalars(
        select(VolunteerSkill.skill_id).where(VolunteerSkill.user_id == volunteer.id)
    )
    skill_ids_list = skill_ids.all()

    if skill_ids_list:
        skills_objects = await db.scalars(
            select(Skill).where(Skill.id.in_(skill_ids_list))
        )
        skills = [s.name for s in skills_objects.all()]
    else:
        skills = []

    if not skills:
        raise HTTPException(status_code=400, detail="У вас не заполнены навыки. Заполните профиль волонтёра.")

    required_skill_map = {
        "transport": ["транспортировка"],
        "vet_help": ["ветпомощь", "инъекции"],
        "socialization": ["социализация", "дрессировка"],
        "repair": ["ремонт"],
        "photography": ["фотосъёмка"],
        "fundraising": ["фандрайзинг"],
    }

    required_skills = required_skill_map.get(task.task_type, [])
    if required_skills and not any(s in skills for s in required_skills):
        raise HTTPException(status_code=400, detail="У вас нет подходящего навыка для этой задачи. Добавьте навык в настройках профиля.")

    response = TaskResponse(
        task_id=task_id,
        volunteer_id=volunteer.id,
        message=payload.message,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)

    # Уведомление сотрудникам организации о новом отклике
    staff_ids = (
        await db.scalars(
            select(OrganizationUser.user_id).where(
                OrganizationUser.organization_id == task.organization_id,
                OrganizationUser.invitation_status == "accepted",
                OrganizationUser.role.in_(["admin", "curator"]),
            )
        )
    ).all()
    for uid in set(staff_ids):
        await create_notification(
            db,
            user_id=uid,
            type="task_response_created",
            title="Новый отклик на задачу",
            body=f"Поступил новый отклик на задачу «{task.title}»",
            data={"task_id": task.id, "response_id": response.id, "volunteer_id": volunteer.id},
            commit=False,
        )
    await db.commit()
    return response


async def get_task_responses_for_curator(
    db: AsyncSession,
    task_id: int,
    curator: User,
) -> list[TaskResponse]:
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    ou = await db.scalar(
        select(OrganizationUser).where(
            OrganizationUser.organization_id == task.organization_id,
            OrganizationUser.user_id == curator.id,
            OrganizationUser.role.in_(["admin", "curator"]),
            OrganizationUser.invitation_status == "accepted",
        )
    )
    if not ou:
        raise HTTPException(status_code=403, detail="Недостаточно прав для просмотра откликов")

    responses = (
        await db.scalars(
            select(TaskResponse)
            .where(TaskResponse.task_id == task_id)
            .order_by(TaskResponse.responded_at.desc())
        )
    ).all()
    return responses


async def update_task_response_status(
    db: AsyncSession,
    response_id: int,
    new_status: str,
    curator: User,
) -> TaskResponse:
    resp = await db.get(TaskResponse, response_id)
    if not resp:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    task = await db.get(Task, resp.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Связанная задача не найдена")

    ou = await db.scalar(
        select(OrganizationUser).where(
            OrganizationUser.organization_id == task.organization_id,
            OrganizationUser.user_id == curator.id,
            OrganizationUser.role.in_(["admin", "curator"]),
            OrganizationUser.invitation_status == "accepted",
        )
    )
    if not ou:
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения статуса отклика")

    if new_status not in {"accepted", "declined"}:
        raise HTTPException(status_code=400, detail="Недопустимый статус")

    resp.status = new_status
    await db.commit()
    await db.refresh(resp)

    # Уведомление волонтёру об изменении статуса отклика
    await create_notification(
        db,
        user_id=resp.volunteer_id,
        type="task_response_status",
        title="Статус отклика изменён",
        body=f"Ваш отклик на задачу «{task.title}»: {new_status}",
        data={"task_id": task.id, "response_id": resp.id, "status": new_status},
        commit=True,
    )

    if new_status == "accepted":
        task.status = "in_progress"
        await db.commit()

    return resp