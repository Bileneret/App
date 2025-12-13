import io
from extensions import db
# ВИПРАВЛЕНО: Додано імпорт User
from models import Application, User


def test_create_application_with_files(client, user):
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    data = {
        "title": "New App",
        "short_description": "Description",
        "files": (io.BytesIO(b"file content"), 'test.txt')
    }

    response = client.post("/applications/new", data=data, content_type='multipart/form-data', follow_redirects=True)
    assert "Заявку успішно створено" in response.get_data(as_text=True)
    assert "test.txt" in response.get_data(as_text=True)


def test_submit_application(client, app, user):
    # 1. Створюємо чернетку
    with app.app_context():
        u = db.session.merge(user)
        app_obj = Application(title="Draft", short_description="Desc", owner=u, status="draft")
        db.session.add(app_obj)
        db.session.commit()
        app_id = app_obj.id

    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    # 2. Подаємо заявку
    response = client.post(f"/applications/{app_id}/submit", follow_redirects=True)
    assert "Заявку подано на розгляд" in response.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(Application, app_id).status == "submitted"


def test_edit_submitted_application_forbidden(client, app, user):
    """Не можна редагувати заявку, яка вже подана."""
    with app.app_context():
        u = db.session.merge(user)
        app_obj = Application(title="Submitted", short_description="Desc", owner=u, status="submitted")
        db.session.add(app_obj)
        db.session.commit()
        app_id = app_obj.id

    client.post("/login", data={"email": user.email, "password": "StrongPass1"})
    response = client.post(f"/applications/{app_id}/edit", data={"title": "New Title"}, follow_redirects=True)

    assert "Редагувати можна лише чернетки" in response.get_data(as_text=True)


def test_access_other_user_application(client, app, user):
    """Користувач не повинен бачити чужі заявки."""
    with app.app_context():
        other_user = User(email="other@test.com", role="applicant")
        other_user.set_password("pass")
        db.session.add(other_user)
        db.session.flush()

        app_obj = Application(title="Secret", short_description="Desc", owner=other_user)
        db.session.add(app_obj)
        db.session.commit()
        app_id = app_obj.id

    client.post("/login", data={"email": user.email, "password": "StrongPass1"})
    response = client.get(f"/applications/{app_id}", follow_redirects=True)

    assert "Ви не маєте доступу" in response.get_data(as_text=True)