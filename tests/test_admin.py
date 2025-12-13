from extensions import db
from models import User


def test_admin_change_role_restriction(client, app, admin):
    """Адмін не може змінювати роль іншого адміна."""
    with app.app_context():
        # Створюємо іншого адміна з паролем
        other_admin = User(email="other_admin@test.com", role="admin")
        other_admin.set_password("admin123")
        db.session.add(other_admin)
        db.session.commit()
        target_id = other_admin.id

    client.post("/login", data={"email": admin.email, "password": "AdminPass1"})

    response = client.post(f"/admin/users/{target_id}/update", data={
        "action": "change_role",
        "role": "applicant"
    }, follow_redirects=True)

    assert "не може редагувати інших адміністраторів" in response.get_data(as_text=True)


def test_admin_block_user(client, app, admin, user):
    """Адмін може заблокувати звичайного користувача."""
    client.post("/login", data={"email": admin.email, "password": "AdminPass1"})

    with app.app_context():
        # ВИПРАВЛЕНО: Використовуємо modern query syntax або db.session.execute
        # Для простоти: беремо ID через select
        target_user = db.session.execute(db.select(User).filter_by(email=user.email)).scalar_one()
        target_id = target_user.id

    response = client.post(f"/admin/users/{target_id}/update", data={
        "action": "toggle_block"
    }, follow_redirects=True)

    assert "заблоковано" in response.get_data(as_text=True)

    with app.app_context():
        # ВИПРАВЛЕНО: db.session.get замість User.query.get
        assert db.session.get(User, target_id).is_blocked is True