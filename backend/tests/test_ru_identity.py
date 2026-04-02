import unittest

from pydantic import ValidationError

from app.core import normalize_ru_mobile, validate_ru_person_name
from app.schemas import LoginRequest, RegisterRequest


class TestNormalizePhone(unittest.TestCase):
    def test_ok_formats(self):
        self.assertEqual(normalize_ru_mobile("+7 (912) 345-67-89"), "+79123456789")
        self.assertEqual(normalize_ru_mobile("89123456789"), "+79123456789")
        self.assertEqual(normalize_ru_mobile("9123456789"), "+79123456789")

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            normalize_ru_mobile("42352435 353")
        with self.assertRaises(ValueError):
            normalize_ru_mobile("+1234567890")
        with self.assertRaises(ValueError):
            normalize_ru_mobile("+7 812 3334455")  # не мобильный (не 9)


class TestPersonName(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(validate_ru_person_name("  Иван  "), "Иван")
        self.assertEqual(validate_ru_person_name("Мария Иванова"), "Мария Иванова")
        self.assertEqual(validate_ru_person_name("Анна-Мария"), "Анна-Мария")

    def test_rejects(self):
        with self.assertRaises(ValueError):
            validate_ru_person_name("ivan")
        with self.assertRaises(ValueError):
            validate_ru_person_name("ИВАН")
        with self.assertRaises(ValueError):
            validate_ru_person_name("John")


class TestRegisterSchema(unittest.TestCase):
    def test_register_ok(self):
        r = RegisterRequest(
            username="damir123",
            password="secret12",
        )
        self.assertEqual(r.username, "damir123")

    def test_register_invalid_username(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(
                username="Дамир123",
                password="secret12",
            )

    def test_login_request(self):
        l = LoginRequest(login="testuser", password="x")
        self.assertEqual(l.login, "testuser")


if __name__ == "__main__":
    unittest.main()
