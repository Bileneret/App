from extensions import db
from models import User


def test_admin_change_role(client, admin):
    # Створюємо юзера
    with client.application.app_context():
        u = User(email="simple@example.com", role="applicant")
        u.set_password("12345678")  # <--- ДОДАНО: Пароль обов'язковий
        db.session.add(u)
        db.session.commit()
        uid = u.id

    client.post("/login", data={"email": admin.email, "password": "admin123"})

    # Змінюємо роль на експерта
    client.post(f"/admin/users/{uid}/update", data={
        "action": "change_role",
        "role": "expert"
    }, follow_redirects=True)

    with client.application.app_context():
        assert db.session.get(User, uid).role == "expert"


def test_admin_block_user(client, admin):
    with client.application.app_context():
        u = User(email="badguy@example.com")
        u.set_password("12345678")  # <--- ДОДАНО
        db.session.add(u)
        db.session.commit()
        uid = u.id

    client.post("/login", data={"email": admin.email, "password": "admin123"})

    response = client.post(f"/admin/users/{uid}/update", data={"action": "toggle_block"}, follow_redirects=True)
    assert "заблоковано" in response.get_data(as_text=True)

    with client.application.app_context():
        assert db.session.get(User, uid).is_blocked is True


def test_admin_cannot_block_super_admin(client, admin):
    """Звичайний адмін не може блокувати супер-адміна."""
    with client.application.app_context():
        sa = User(email="super@example.com", role="super_admin")
        sa.set_password("12345678")  # <--- ДОДАНО
        db.session.add(sa)
        db.session.commit()
        sa_id = sa.id

    client.post("/login", data={"email": admin.email, "password": "admin123"})

    response = client.post(f"/admin/users/{sa_id}/update", data={"action": "toggle_block"}, follow_redirects=True)
    # Перевіряємо наявність повідомлення про помилку
    assert "не можете" in response.get_data(as_text=True)

    with client.application.app_context():
        assert db.session.get(User, sa_id).is_blocked is False


def test_admin_stats_page(client, admin):
    client.post("/login", data={"email": admin.email, "password": "admin123"})
    response = client.get("/admin/stats")
    assert response.status_code == 200
    assert "Статистика системи" in response.get_data(as_text=True)