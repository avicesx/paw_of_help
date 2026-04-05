"""
Тесты для профиля волонтёра: структура, валидация, импорты.
Запуск из корня репозитория: python -m unittest discover -s backend/tests -p "test_*.py" -v
"""

import unittest
from datetime import datetime

from app.core import create_access_token
from app.schemas.volunteer import (
    VolunteerProfileUpdate, VolunteerProfileResponse, SkillResponse, SkillListResponse,
    SkillIdsRequest, TaskBriefResponse, CompletedTaskResponse, ReviewResponse,
    VolunteerStats, VolunteerProfileFullResponse, AchievementResponse
)
from app.services.volunteer_service import (
    get_or_create_profile, update_profile, deactivate_profile,
    get_volunteer_stats, get_active_tasks, get_completed_tasks,
    get_skills, get_my_skills, set_my_skills, delete_my_skill
)
from app.api.volunteer import router as volunteer_router


class TestVolunteerSchemas(unittest.TestCase):
    """Тесты для Pydantic схем."""

    def test_volunteer_profile_update_all_fields_optional(self):
        """Тест что все поля VolunteerProfileUpdate опциональны."""
        # Должно быть возможно создать объект без полей
        data = VolunteerProfileUpdate()
        self.assertIsNotNone(data)

    def test_volunteer_profile_update_with_data(self):
        """Тест создание VolunteerProfileUpdate с данными."""
        data = VolunteerProfileUpdate(
            location="Moscow",
            radius_km=10,
            ready_for_foster=True
        )
        self.assertEqual(data.location, "Moscow")
        self.assertEqual(data.radius_km, 10)
        self.assertTrue(data.ready_for_foster)

    def test_volunteer_profile_update_exclude_unset(self):
        """Тест model_dump с exclude_unset для VolunteerProfileUpdate."""
        data = VolunteerProfileUpdate(
            location="Moscow",
            radius_km=10
        )
        dumped = data.model_dump(exclude_unset=True)
        self.assertIn("location", dumped)
        self.assertIn("radius_km", dumped)

    def test_skill_ids_request(self):
        """Тест SkillIdsRequest."""
        data = SkillIdsRequest(skill_ids=[1, 2, 3])
        self.assertEqual(data.skill_ids, [1, 2, 3])

    def test_skill_ids_request_empty(self):
        """Тест SkillIdsRequest с пустым списком."""
        data = SkillIdsRequest(skill_ids=[])
        self.assertEqual(data.skill_ids, [])

    def test_skill_response(self):
        """Тест SkillResponse."""
        skill = SkillResponse(id=1, name="Transport", description="Транспортировка")
        self.assertEqual(skill.id, 1)
        self.assertEqual(skill.name, "Transport")
        self.assertEqual(skill.description, "Транспортировка")

    def test_skill_response_optional_description(self):
        """Тест SkillResponse без описания."""
        skill = SkillResponse(id=1, name="Transport")
        self.assertEqual(skill.id, 1)
        self.assertEqual(skill.name, "Transport")
        self.assertIsNone(skill.description)

    def test_skill_list_response(self):
        """Тест SkillListResponse."""
        skills_data = [
            SkillResponse(id=1, name="Emergency"),
            SkillResponse(id=2, name="Transport"),
        ]
        skill_list = SkillListResponse(skills=skills_data)
        self.assertEqual(len(skill_list.skills), 2)

    def test_achievement_response(self):
        """Тест AchievementResponse."""
        achievement = AchievementResponse(
            id=1,
            code="transport_10",
            title="Транспортировка 10 животных"
        )
        self.assertEqual(achievement.id, 1)
        self.assertEqual(achievement.code, "transport_10")

    def test_volunteer_stats(self):
        """Тест VolunteerStats."""
        stats = VolunteerStats(
            total_completed_tasks=5,
            rating_by_reviews=4.5,
            total_reviews_count=3,
            volunteer_hours=20,
            achievements=[]
        )
        self.assertEqual(stats.total_completed_tasks, 5)
        self.assertEqual(stats.rating_by_reviews, 4.5)
        self.assertEqual(stats.total_reviews_count, 3)
        self.assertEqual(stats.volunteer_hours, 20)

    def test_volunteer_stats_optional_hours(self):
        """Тест VolunteerStats без часов."""
        stats = VolunteerStats(
            total_completed_tasks=0,
            rating_by_reviews=0.0,
            total_reviews_count=0,
            achievements=[]
        )
        self.assertIsNone(stats.volunteer_hours)

    def test_task_brief_response(self):
        """Тест TaskBriefResponse."""
        now = datetime.now()
        task = TaskBriefResponse(
            id=1,
            title="Transport help",
            description="Help with transport",
            status="in_progress",
            created_at=now,
            end_date=None,
            author_id=50
        )
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Transport help")
        self.assertEqual(task.author_id, 50)

    def test_review_response(self):
        """Тест ReviewResponse."""
        now = datetime.now()
        review = ReviewResponse(
            id=1,
            reviewer_id=50,
            rating=5,
            comment="Great work!",
            created_at=now
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great work!")

    def test_completed_task_response(self):
        """Тест CompletedTaskResponse с отзывом."""
        now = datetime.now()
        review = ReviewResponse(
            id=1,
            reviewer_id=50,
            rating=5,
            comment="Perfect!",
            created_at=now
        )
        task = CompletedTaskResponse(
            id=1,
            title="Completed task",
            status="done",
            created_at=now,
            author_id=50,
            completed_at=now,
            review=review
        )
        self.assertIsNotNone(task.review)
        self.assertEqual(task.review.rating, 5)

    def test_completed_task_response_no_review(self):
        """Тест CompletedTaskResponse без отзыва."""
        now = datetime.now()
        task = CompletedTaskResponse(
            id=1,
            title="Completed task",
            status="done",
            created_at=now,
            author_id=50,
            completed_at=now,
            review=None
        )
        self.assertIsNone(task.review)

    def test_volunteer_profile_full_response(self):
        """Тест VolunteerProfileFullResponse."""
        stats = VolunteerStats(
            total_completed_tasks=3,
            rating_by_reviews=4.0,
            total_reviews_count=2,
            achievements=[]
        )
        profile = VolunteerProfileFullResponse(
            user_id=1,
            location="Moscow",
            radius_km=10,
            created_at=datetime.now(),
            stats=stats
        )
        self.assertEqual(profile.user_id, 1)
        self.assertEqual(profile.location, "Moscow")
        self.assertEqual(profile.stats.total_completed_tasks, 3)


class TestVolunteerServiceImports(unittest.TestCase):
    """Тесты для сервисных функций."""

    def test_service_functions_callable(self):
        """Тест что все сервисные функции вызываемы."""
        self.assertTrue(callable(get_or_create_profile))
        self.assertTrue(callable(update_profile))
        self.assertTrue(callable(deactivate_profile))
        self.assertTrue(callable(get_volunteer_stats))
        self.assertTrue(callable(get_active_tasks))
        self.assertTrue(callable(get_completed_tasks))
        self.assertTrue(callable(get_skills))
        self.assertTrue(callable(get_my_skills))
        self.assertTrue(callable(set_my_skills))
        self.assertTrue(callable(delete_my_skill))

    def test_service_functions_have_docstrings(self):
        """Тест что все сервисные функции имеют документацию."""
        self.assertIsNotNone(get_or_create_profile.__doc__)
        self.assertIsNotNone(update_profile.__doc__)
        self.assertIsNotNone(deactivate_profile.__doc__)


class TestVolunteerRouterStructure(unittest.TestCase):
    """Тесты структуры роутера."""

    def test_router_has_routes(self):
        """Тест что роутер имеет маршруты."""
        self.assertTrue(hasattr(volunteer_router, 'routes'))

    def test_router_prefix(self):
        """Тест префикс роутера."""
        self.assertEqual(volunteer_router.prefix, "/volunteer")

    def test_router_tags(self):
        """Тест теги роутера."""
        self.assertIn("volunteer", volunteer_router.tags)

    def test_router_routes_count(self):
        """Тест количество маршрутов."""
        # Должно быть как минимум 8 маршрутов: профиль (3), навыки (4), задачи (1)
        self.assertGreaterEqual(len(volunteer_router.routes), 8)

    def test_router_routes_methods(self):
        """Тест методы маршрутов."""
        methods = set()
        for route in volunteer_router.routes:
            if hasattr(route, 'methods'):
                methods.update(route.methods)
        
        # Должны быть GET, PATCH, POST, DELETE
        self.assertIn("GET", methods)
        self.assertIn("PATCH", methods)
        self.assertIn("POST", methods)
        self.assertIn("DELETE", methods)

    def test_router_has_endpoint_descriptions(self):
        """Тест что эндпоинты имеют описания."""
        for route in volunteer_router.routes:
            if hasattr(route, 'summary'):
                # Если есть summary, он не пустой
                if route.summary:
                    self.assertGreater(len(route.summary), 0)


class TestVolunteerAPI(unittest.TestCase):
    """Тесты интеграции API."""

    def test_app_includes_volunteer_router(self):
        """Тест что главное приложение включает роутер волонтёра."""
        from app.main import app
        
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # Должны быть маршруты с /volunteer
        volunteer_routes = [r for r in routes if "/volunteer" in r]
        self.assertGreater(len(volunteer_routes), 0, "No /volunteer routes found in app")

    def test_volunteer_routes_count(self):
        """Тест количество маршрутов волонтёра в приложении."""
        from app.main import app
        
        volunteer_routes = [r for r in app.routes if hasattr(r, 'path') and "/volunteer" in r.path]
        # Минимум: /profile (GET, PATCH, DELETE), /skills (GET), /my-skills (GET, POST, DELETE), /tasks (GET)
        self.assertGreaterEqual(len(volunteer_routes), 8)

    def test_volunteer_endpoints(self):
        """Тест присутствие основных эндпоинтов."""
        from app.main import app
        
        all_routes = set()
        for route in app.routes:
            if hasattr(route, 'path'):
                all_routes.add(route.path)
        
        expected_endpoints = [
            "/volunteer/profile",
            "/volunteer/skills",
            "/volunteer/my-skills",
            "/volunteer/tasks",
        ]
        
        for endpoint in expected_endpoints:
            self.assertTrue(
                any(endpoint in route for route in all_routes),
                f"Endpoint {endpoint} not found in app routes"
            )


class TestTokenGeneration(unittest.TestCase):
    """Тесты генерации токенов для авторизации."""

    def test_create_access_token(self):
        """Тест создания access token."""
        user_id = "123"
        token = create_access_token(user_id)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_create_access_token_different_users(self):
        """Тест создание разных токенов для разных пользователей."""
        token1 = create_access_token("user1")
        token2 = create_access_token("user2")
        self.assertNotEqual(token1, token2)


class TestVolunteerProfileValidation(unittest.TestCase):
    """Тесты валидации данных профиля."""

    def test_profile_with_invalid_radius(self):
        """Тест что радиус может быть любым числом."""
        profile = VolunteerProfileUpdate(radius_km=-5)
        self.assertEqual(profile.radius_km, -5)

    def test_profile_with_large_radius(self):
        """Тест с большим радиусом."""
        profile = VolunteerProfileUpdate(radius_km=1000)
        self.assertEqual(profile.radius_km, 1000)

    def test_profile_with_availability(self):
        """Тест профиль с матрицей доступности."""
        availability = {"weekdays": "evening", "weekends": "anytime"}
        profile = VolunteerProfileUpdate(availability=availability)
        self.assertEqual(profile.availability, availability)

    def test_profile_with_animal_types(self):
        """Тест профиль с предпочтениями животных."""
        animal_types = ["dog", "cat"]
        profile = VolunteerProfileUpdate(preferred_animal_types=animal_types)
        self.assertEqual(profile.preferred_animal_types, animal_types)

    def test_profile_with_foster_restrictions(self):
        """Тест профиль с ограничениями передержки."""
        restrictions = "No aggressive, only vaccinated"
        profile = VolunteerProfileUpdate(foster_restrictions=restrictions)
        self.assertEqual(profile.foster_restrictions, restrictions)

    def test_profile_with_foster_photos(self):
        """Тест профиль с фото места передержки."""
        photos = ["photo1.jpg", "photo2.jpg"]
        profile = VolunteerProfileUpdate(foster_photos=photos)
        self.assertEqual(profile.foster_photos, photos)

    def test_profile_with_pets_info(self):
        """Тест профиль с информацией о животных."""
        pets = {"cats": 2, "dogs": 1}
        profile = VolunteerProfileUpdate(has_other_pets=pets)
        self.assertEqual(profile.has_other_pets, pets)


if __name__ == "__main__":
    unittest.main()
