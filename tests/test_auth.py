from unittest.mock import patch, MagicMock
from extensions import db
from models import User


def test_register_success(client):
    """Успішна реєстрація нового користувача (з імітацією валідації email)."""
    # Імітуємо (mock) успішну перевірку email, щоб не залежати від DNS/Інтернету
    with patch("auth_routes.validate_email") as mock_validate:
        # Налаштовуємо мок: він повертає об'єкт, у якого є поле email
        mock_obj = MagicMock()
        mock_obj.email = "new@example.com"
        mock_validate.return_value = mock_obj

        response = client.post(
            "/register",
            data={
                "email": "new@example.com",
                "password": "StrongPass1",
                "confirm_password": "StrongPass1",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "Реєстрація успішна" in response.get_data(as_text=True)


def test_register_fail_passwords_mismatch(client):
    """Перевірка помилки при неспівпадінні паролів."""
    response = client.post("/register", data={
        "email": "fail@example.com",
        "password": "Password123",
        "confirm_password": "WrongPassword"
    }, follow_redirects=True)
    assert "Паролі не співпадають" in response.get_data(as_text=True)


def test_login_logout(client, user):
    """Перевірка входу та виходу."""
    response = client.post("/login", data={
        "email": user.email,
        "password": "StrongPass1"
    }, follow_redirects=True)
    assert "Ви успішно увійшли" in response.get_data(as_text=True)

    response = client.get("/logout", follow_redirects=True)
    assert "Ви вийшли із системи" in response.get_data(as_text=True)


def test_change_password(client, user):
    """Перевірка зміни пароля."""
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    response = client.post("/profile/password", data={
        "current_password": "StrongPass1",
        "new_password": "NewPassword123",
        "confirm_password": "NewPassword123"
    }, follow_redirects=True)

    assert "Пароль успішно змінено" in response.get_data(as_text=True)

    with client.application.app_context():
        u = db.session.get(User, user.id)
        assert u.check_password("NewPassword123")