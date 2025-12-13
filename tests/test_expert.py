from extensions import db
from models import User, Application
from unittest.mock import patch


def test_expert_dashboard(client, expert_headers):
    """Тест доступу до кабінету експерта."""
    response = client.get("/expert/applications", headers=expert_headers)
    assert response.status_code == 200
    assert "Заявки на розгляді" in response.get_data(as_text=True)


def test_expert_can_approve_application(client, app, auth_headers):
    """Сценарій: Юзер подає заявку -> Експерт схвалює."""
    # 1. Юзер створює та подає (клієнт зараз авторизований як applicant через auth_headers)
    client.post("/applications/new", data={"title": "For Expert", "short_description": "Desc"}, headers=auth_headers)

    with app.app_context():
        app_obj = Application.query.filter_by(title="For Expert").first()
        app_id = app_obj.id

    client.post(f"/applications/{app_id}/submit", headers=auth_headers)

    # 2. ЗМІНА КОРИСТУВАЧА: Вихід юзера -> Вхід Експерта
    client.get("/logout")

    # Створюємо експерта, якщо ще немає
    with app.app_context():
        if not User.query.filter_by(email="expert_flow@test.com").first():
            expert = User(email="expert_flow@test.com", role="expert")
            expert.set_password("password")
            db.session.add(expert)
            db.session.commit()

    client.post("/login", data={"email": "expert_flow@test.com", "password": "password"})

    # 3. Експерт оцінює (мок пошти, щоб не було SMTP помилок)
    with patch("expert_routes.send_status_update_email"):
        response = client.post(
            f"/expert/applications/{app_id}",
            data={"decision": "approved", "comment": "Good job"},
            follow_redirects=True
        )

    assert response.status_code == 200
    # Перевіряємо наявність флеш-повідомлення (українською або англійською)
    assert "Заявку переведено у статус: approved" in response.get_data(as_text=True)


def test_expert_invalid_decision(client, app, auth_headers):
    """Тест відправки невалідного рішення."""
    # 1. Створюємо заявку
    client.post("/applications/new", data={"title": "Bad Request", "short_description": "D"}, headers=auth_headers)
    with app.app_context():
        app_id = Application.query.filter_by(title="Bad Request").first().id
    client.post(f"/applications/{app_id}/submit", headers=auth_headers)

    # 2. Логін як експерт
    client.get("/logout")
    with app.app_context():
        if not User.query.filter_by(email="expert_inv@test.com").first():
            e = User(email="expert_inv@test.com", role="expert")
            e.set_password("p")
            db.session.add(e)
            db.session.commit()
    client.post("/login", data={"email": "expert_inv@test.com", "password": "p"})

    # 3. Відправляємо неіснуючий статус
    response = client.post(
        f"/expert/applications/{app_id}",
        data={"decision": "super_status", "comment": ""},
        follow_redirects=True
    )
    assert "Невірний статус рішення" in response.get_data(as_text=True)


def test_expert_cannot_review_own_app(client, app):
    """Експерт не може оцінювати власну заявку."""
    # 1. Експерт створює власну заявку
    with app.app_context():
        if not User.query.filter_by(email="expert_own@test.com").first():
            e = User(email="expert_own@test.com", role="expert")
            e.set_password("p")
            db.session.add(e)
            db.session.commit()

    client.post("/login", data={"email": "expert_own@test.com", "password": "p"})
    client.post("/applications/new", data={'title': 'My App', 'short_description': '...'}, follow_redirects=True)

    with app.app_context():
        app_id = Application.query.filter_by(title="My App").first().id

    # 2. Спроба зайти на сторінку оцінки
    response = client.get(f"/expert/applications/{app_id}", follow_redirects=True)
    assert "Ви не можете оцінювати власні заявки" in response.get_data(as_text=True)