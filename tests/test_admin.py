from extensions import db
from models import User


def test_admin_can_view_users_list(client, app):
    """Перевірка доступу адміна до списку користувачів."""
    # 1. Створюємо Адміна
    with app.app_context():
        # Перевіряємо на всяк випадок, хоча база чиста
        if not User.query.filter_by(email="admin_test@test.com").first():
            admin = User(email="admin_test@test.com", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    # 2. Логінимось
    client.post("/login", data={"email": "admin_test@test.com", "password": "admin123"})

    # 3. Заходимо на сторінку адміністрування
    response = client.get("/admin/users")

    assert response.status_code == 200
    # ВИПРАВЛЕНО: Шукаємо текст, який точно є в шаблоні (title)
    assert "Адміністрування користувачів" in response.get_data(as_text=True)


def test_admin_can_block_user(client, app):
    """Перевірка блокування користувача."""
    # 1. Підготовка: створюємо юзера І АДМІНА (бо база очищається)
    with app.app_context():
        # Створюємо адміна ЗНОВУ
        admin = User(email="admin_test@test.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # Створюємо юзера для блокування
        user_to_block = User(email="bad_user@test.com", role="applicant")
        user_to_block.set_password("12345678")
        db.session.add(user_to_block)

        db.session.commit()
        user_id = user_to_block.id

    # 2. Логінимось як Адмін
    client.post("/login", data={"email": "admin_test@test.com", "password": "admin123"})

    # 3. Відправляємо запит на блокування
    response = client.post(
        f"/admin/users/{user_id}/update",
        data={"action": "toggle_block"},
        follow_redirects=True
    )

    assert response.status_code == 200
    # Текст з admin_routes.py: "Користувача ... заблоковано."
    assert "заблоковано" in response.get_data(as_text=True)

    # 4. Перевіряємо в БД, чи змінився статус
    with app.app_context():
        blocked_user = db.session.get(User, user_id)
        assert blocked_user.is_blocked is True