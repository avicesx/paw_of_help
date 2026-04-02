"""
API-тесты auth с подменой БД (без реального PostgreSQL).
Запуск из корня репозитория: python -m unittest discover -s backend/tests -p \"test_*.py\" -v
"""

import unittest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
import jwt as pyjwt

from app.core import settings, get_db, create_access_token, get_password_hash
from app.main import app
from app.models import User


async def _session_register_success():
    session = AsyncMock()

    async def refresh(u, **kwargs):
        object.__setattr__(u, "id", 101)

    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock(side_effect=refresh)
    yield session


async def _session_register_conflict_username():
    existing = MagicMock()
    existing.username = "conflictuser"
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=existing)
    yield session


async def _session_login_success():
    u = User(
        id=55,
        email="login@test.ru",
        phone=None,
        username="testuser",
        password_hash=get_password_hash("CorrectHorse-99"),
        name=None,
        is_active=True,
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=u)
    session.commit = AsyncMock()
    yield session


async def _session_login_no_user():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    yield session


async def _session_login_inactive():
    u = User(
        id=55,
        email="blocked@test.ru",
        phone=None,
        username="blockeduser",
        password_hash=get_password_hash("SamePass-1"),
        name=None,
        is_active=False,
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=u)
    session.commit = AsyncMock()
    yield session


async def _session_me_user():
    u = User(
        id=77,
        name=None,
        email="maria@test.ru",
        phone=None,
        username="mariauser",
        password_hash="x",
        is_active=True,
    )
    session = AsyncMock()
    session.get = AsyncMock(return_value=u)
    yield session


class TestAuthAPI(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_register_validation_422_username(self):
        app.dependency_overrides[get_db] = _session_register_success
        with TestClient(app) as client:
            r = client.post(
                "/auth/register",
                json={
                    "username": "Иван123",
                    "password": "secret12",
                },
            )
        self.assertEqual(r.status_code, 422)

    def test_register_success_and_jwt(self):
        app.dependency_overrides[get_db] = _session_register_success
        with TestClient(app) as client:
            r = client.post(
                "/auth/register",
                json={
                    "username": "newuser",
                    "password": "secret12",
                },
            )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIn("access_token", body)
        decoded = pyjwt.decode(
            body["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        self.assertEqual(decoded["sub"], "101")

    def test_register_conflict_409(self):
        app.dependency_overrides[get_db] = _session_register_conflict_username
        with TestClient(app) as client:
            r = client.post(
                "/auth/register",
                json={
                    "username": "conflictuser",
                    "password": "secret12",
                },
            )
        self.assertEqual(r.status_code, 409)

    def test_login_success(self):
        app.dependency_overrides[get_db] = _session_login_success
        with TestClient(app) as client:
            r = client.post(
                "/auth/login",
                json={"login": "testuser", "password": "CorrectHorse-99"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        decoded = pyjwt.decode(
            r.json()["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        self.assertEqual(decoded["sub"], "55")

    def test_login_unknown_401(self):
        app.dependency_overrides[get_db] = _session_login_no_user
        with TestClient(app) as client:
            r = client.post(
                "/auth/login",
                json={"login": "nobody", "password": "any"},
            )
        self.assertEqual(r.status_code, 401)

    def test_login_inactive_403(self):
        app.dependency_overrides[get_db] = _session_login_inactive
        with TestClient(app) as client:
            r = client.post(
                "/auth/login",
                json={"login": "blockeduser", "password": "SamePass-1"},
            )
        self.assertEqual(r.status_code, 403)

    def test_me_with_bearer(self):
        app.dependency_overrides[get_db] = _session_me_user
        token = create_access_token("77")
        with TestClient(app) as client:
            r = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["id"], 77)
        self.assertEqual(data["name"], None)
        self.assertEqual(data["username"], "mariauser")
        self.assertEqual(data["email"], "maria@test.ru")


if __name__ == "__main__":
    unittest.main()
