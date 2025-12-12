from extensions import db
from models import Application


def test_create_application_success(client, app, user):
    """Перевірка створення заявки (має стати Draft)."""
    # 1. Логінимось
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    # 2. Створюємо заявку
    response = client.post(
        "/applications/new",
        data={
            "title": "Тестова заявка",
            "short_description": "Опис винаходу"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "Заявку створено як чернетку" in response.get_data(as_text=True)

    # 3. Перевіряємо в БД
    with app.app_context():
        # Шукаємо заявку в базі
        app_db = Application.query.filter_by(title="Тестова заявка").first()
        assert app_db is not None
        assert app_db.status == "draft"


def test_submit_application_changes_status(client, app, user):
    """Перевірка подачі заявки (Draft -> Submitted)."""
    # 1. Логін
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    # 2. Створюємо заявку (через клієнт, щоб імітувати реального користувача)
    client.post("/applications/new", data={"title": "App to Submit", "short_description": "Desc"})

    # Отримуємо ID нової заявки з бази
    with app.app_context():
        app_id = Application.query.filter_by(title="App to Submit").first().id

    # 3. Натискаємо кнопку "Подати" (імітація POST запиту)
    response = client.post(f"/applications/{app_id}/submit", follow_redirects=True)

    assert response.status_code == 200
    assert "Заявку подано на розгляд" in response.get_data(as_text=True)

    # 4. Перевіряємо, чи змінився статус
    with app.app_context():
        updated_app = db.session.get(Application, app_id)
        assert updated_app.status == "submitted"