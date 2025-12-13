from unittest.mock import patch, MagicMock
from models import User, PasswordResetToken


def test_register_success(client):
    # ВИПРАВЛЕНО: Мокаємо валідацію email, щоб уникнути DNS запитів
    with patch("auth_routes.validate_email") as mock_validate:
        # Налаштовуємо mock, щоб він повертав об'єкт з атрибутом email
        mock_success = MagicMock()
        mock_success.email = "newuser@example.com"
        mock_validate.return_value = mock_success

        response = client.post("/register", data={
            "email": "newuser@example.com",
            "password": "Password123",
            "confirm_password": "Password123"
        }, follow_redirects=True)

        assert response.status_code == 200
        assert "Реєстрація успішна" in response.get_data(as_text=True)


def test_register_validation_errors(client, user):
    """Перевірка валідації: існуючий email та короткий пароль."""
    # Тут теж краще замокати, хоча email і так існує, але щоб не було DNS помилок
    with patch("auth_routes.validate_email") as mock_validate:
        mock_success = MagicMock()
        mock_success.email = user.email
        mock_validate.return_value = mock_success

        response = client.post("/register", data={
            "email": user.email,  # Вже існує
            "password": "123",  # Закороткий
            "confirm_password": "123"
        }, follow_redirects=True)

        text = response.get_data(as_text=True)
        assert "Користувач з таким e-mail уже зареєстрований" in text
        assert "Пароль має містити щонайменше 8 символів" in text


def test_login_blocked_user(client, app):
    """Перевірка, що заблокований користувач не може увійти."""
    with app.app_context():
        u = User(email="blocked@test.com", is_blocked=True)
        u.set_password("Password123")
        from extensions import db
        db.session.add(u)
        db.session.commit()

    response = client.post("/login", data={
        "email": "blocked@test.com",
        "password": "Password123"
    }, follow_redirects=True)

    assert "Ваш акаунт заблоковано" in response.get_data(as_text=True)


def test_password_reset_flow(client, app, user):
    """Тест повного циклу відновлення пароля."""
    # 1. Запит на відновлення
    with patch("auth_routes.send_password_reset_email") as mock_send:
        client.post("/password/reset/request", data={"email": user.email})
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        reset_link = args[1]
        token = reset_link.split("/")[-1]

    # 2. Використання токена
    response = client.post(f"/password/reset/{token}", data={
        "password": "NewPassword123",
        "confirm_password": "NewPassword123"
    }, follow_redirects=True)

    assert "Пароль успішно змінено" in response.get_data(as_text=True)

    # 3. Перевірка входу з новим паролем
    login_resp = client.post("/login", data={
        "email": user.email,
        "password": "NewPassword123"
    }, follow_redirects=True)
    assert "Ви успішно увійшли" in login_resp.get_data(as_text=True)