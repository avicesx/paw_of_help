Открывай страницы из frontend/pages/.
Основные новые страницы:
- profile.html
- settings.html
- tasks.html
- reviews.html
- complaints.html

Что переведено с заглушек на backend:
- задачи -> /tasks
- создание задачи -> /tasks/organizations/{org_id}
- смена статуса задачи -> PATCH /tasks/{task_id}
- выбор животных -> /animals
- настройки аккаунта -> /users/me
- смена пароля -> /users/me/change-password
- профиль волонтёра -> /volunteer/profile
- отзывы -> /reviews

Что осталось заглушкой:
- жалобы (на backend эндпоинтов нет)
- org_id для задач хранится во frontend через localStorage key paw_org_id
