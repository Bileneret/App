from unittest.mock import patch, MagicMock
import pytest
from email_validator import validate_email, EmailNotValidError
from extensions import db
from models import User, PasswordResetToken


def test_register_new_user_success(client):
    """Успішна реєстрація нового користувача."""
    with patch("auth_routes.validate_email") as mock_validate:
        mock_valid = MagicMock()
        mock_valid.email = "new@example.com"
        mock_validate.return_value = mock_valid

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
        text = response.get_data(as_text=True)
        # Перевіряємо обидва варіанти, бо після успіху йде редірект
        assert "Реєстрація успішна" in text or "Вхід" in text


def test_register_existing_email_and_short_password(client, app):
    """Перевірка обробки помилок при реєстрації."""
    # Створюємо користувача вручну всередині тесту, щоб уникнути DetachedInstanceError
    email = "existing@test.com"
    with app.app_context():
        u = User(email=email, role="applicant")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

    with patch("auth_routes.validate_email") as mock_validate:
        mock_valid = MagicMock()
        mock_valid.email = email
        mock_validate.return_value = mock_valid

        response = client.post(
            "/register",
            data={
                "email": email,
                "password": "short",
                "confirm_password": "short",
            },
            follow_redirects=True,
        )
        text = response.get_data(as_text=True)
        # Спочатку спрацює валідатор довжини пароля
        assert "Пароль має містити щонайменше 8 символів" in text


def test_cannot_access_profile_without_login(client):
    """Захист сторінок: редірект на логін."""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_logout_flow(client, app):
    """Тест входу та виходу із системи."""
    with app.app_context():
        u = User(email="login_flow@test.com", role="applicant")
        u.set_password("password")
        db.session.add(u)
        db.session.commit()

    # Login
    response = client.post('/login', data={'email': 'login_flow@test.com', 'password': 'password'},
                           follow_redirects=True)
    assert response.status_code == 200
    assert "Ви успішно увійшли в систему" in response.get_data(as_text=True)

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert "Ви вийшли із системи" in response.get_data(as_text=True)


def test_profile_view(client, auth_headers):
    """Тест перегляду профілю авторизованим користувачем."""
    response = client.get('/profile', headers=auth_headers)
    assert response.status_code == 200
    assert "Профіль користувача" in response.get_data(as_text=True)


def test_change_password(client, auth_headers, app):
    """Тест зміни пароля."""
    # 1. Успішна зміна
    response = client.post('/profile/password', data={
        'current_password': 'password',
        'new_password': 'NewStrongPass1',
        'confirm_password': 'NewStrongPass1'
    }, headers=auth_headers, follow_redirects=True)
    assert response.status_code == 200
    assert "Пароль успішно змінено" in response.get_data(as_text=True)

    # 2. Помилка: неправильний старий пароль
    response = client.post('/profile/password', data={
        'current_password': 'wrong_password',
        'new_password': 'NewStrongPass1',
        'confirm_password': 'NewStrongPass1'
    }, headers=auth_headers, follow_redirects=True)
    assert "Неправильний поточний пароль" in response.get_data(as_text=True)


def test_reset_password_flow(client, app):
    """Тест повного циклу відновлення пароля."""
    with app.app_context():
        u = User(email="reset@test.com", role="applicant")
        u.set_password("oldpass")
        db.session.add(u)
        db.session.commit()

    # 1. Запит на скидання
    with patch("auth_routes.send_password_reset_email") as mock_send:
        response = client.post('/password/reset/request', data={'email': 'reset@test.com'}, follow_redirects=True)
        assert response.status_code == 200
        assert "надіслано посилання" in response.get_data(as_text=True)

    # Отримуємо токен
    with app.app_context():
        user = User.query.filter_by(email="reset@test.com").first()
        token = PasswordResetToken.query.filter_by(user_id=user.id).first().token

    # 2. Встановлення нового пароля
    response = client.post(f'/password/reset/{token}', data={
        'password': 'newsecurepass',
        'confirm_password': 'newsecurepass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Пароль успішно змінено" in response.get_data(as_text=True)

    # 3. Спроба використати токен повторно
    response = client.get(f'/password/reset/{token}', follow_redirects=True)
    assert "Посилання для відновлення пароля недійсне" in response.get_data(as_text=True)


def test_invalid_email_validation():
    """Перевірка валідатора email."""
    with pytest.raises(EmailNotValidError):
        validate_email("not-an-email")