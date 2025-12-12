from extensions import db
from models import User, Application


def test_expert_can_approve_application(client, app, user):
    """
    Сценарій:
    1. Звичайний користувач створює і подає заявку.
    2. Експерт заходить у систему.
    3. Експерт бачить цю заявку.
    4. Експерт схвалює її (Approved).
    """

    # --- ЧАСТИНА 1: Підготовка (Створення заявки користувачем) ---
    # Логінимось як звичайний юзер
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    # Створюємо заявку
    client.post("/applications/new", data={"title": "Заявка для Експертизи", "short_description": "Опис"})

    # Отримуємо ID заявки і подаємо її (Submit)
    with app.app_context():
        app_obj = Application.query.filter_by(title="Заявка для Експертизи").first()
        app_id = app_obj.id

    client.post(f"/applications/{app_id}/submit", follow_redirects=True)
    client.get("/logout")  # Виходимо

    # --- ЧАСТИНА 2: Дії Експерта ---

    # Створюємо експерта в базі даних (якщо його там ще немає в тестовій БД)
    with app.app_context():
        expert = User(email="expert@test.com", role="expert")
        expert.set_password("expert123")
        db.session.add(expert)
        db.session.commit()

    # Логінимось як Експерт
    client.post("/login", data={"email": "expert@test.com", "password": "expert123"})

    # Перевіряємо, чи бачить експерт заявку на дашборді
    resp_dashboard = client.get("/expert/applications")
    assert resp_dashboard.status_code == 200
    assert "Заявка для Експертизи" in resp_dashboard.get_data(as_text=True)

    # Експерт схвалює заявку (Approved)
    resp_approve = client.post(
        f"/expert/applications/{app_id}",
        data={"decision": "approved", "comment": "Чудова робота!"},
        follow_redirects=True
    )

    assert resp_approve.status_code == 200
    assert "Заявку переведено у статус: approved" in resp_approve.get_data(as_text=True)

    # --- ЧАСТИНА 3: Фінальна перевірка в БД ---
    with app.app_context():
        updated_app = db.session.get(Application, app_id)
        assert updated_app.status == "approved"
        assert updated_app.expert_comment == "Чудова робота!"