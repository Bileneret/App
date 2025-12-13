import io
from extensions import db
from models import Application, ApplicationFile, User


def get_app_by_title(title):
    """Допоміжна функція для отримання заявки без Legacy API."""
    return db.session.execute(
        db.select(Application).filter_by(title=title)
    ).scalar_one_or_none()


def test_create_application_success(client, user):
    """Перевірка створення заявки (має стати Draft)."""
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    response = client.post(
        "/applications/new",
        data={
            "title": "Тестова заявка",
            "short_description": "Опис винаходу"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "Заявку успішно створено" in response.get_data(as_text=True)

    with client.application.app_context():
        app_db = get_app_by_title("Тестова заявка")
        assert app_db is not None
        assert app_db.status == "draft"


def test_create_application_with_file(client, user):
    """Створення заявки з файлом."""
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    data = {
        "title": "Test App",
        "short_description": "Description",
        "files": (io.BytesIO(b"file content"), "test_doc.txt")
    }

    response = client.post("/applications/new", data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert "Заявку успішно створено" in response.get_data(as_text=True)

    with client.application.app_context():
        app_obj = get_app_by_title("Test App")
        assert len(app_obj.files) == 1
        assert "test_doc.txt" in app_obj.files[0].filename


def test_edit_application_add_file(client, user):
    """Редагування заявки та додавання файлу."""
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})
    client.post("/applications/new", data={"title": "Draft App", "short_description": "Desc"})

    with client.application.app_context():
        app_id = get_app_by_title("Draft App").id

    data = {
        "title": "Updated Title",
        "short_description": "Updated Desc",
        "files": (io.BytesIO(b"new content"), "new_file.pdf")
    }
    response = client.post(f"/applications/{app_id}/edit", data=data, content_type='multipart/form-data',
                           follow_redirects=True)

    assert "Заявку оновлено" in response.get_data(as_text=True)


def test_submit_and_cancel_application(client, user):
    """Подача та скасування заявки."""
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})
    client.post("/applications/new", data={"title": "To Submit", "short_description": "..."})

    with client.application.app_context():
        app_id = get_app_by_title("To Submit").id

    # Submit
    client.post(f"/applications/{app_id}/submit", follow_redirects=True)
    with client.application.app_context():
        assert db.session.get(Application, app_id).status == "submitted"

    # Cancel
    client.post(f"/applications/{app_id}/cancel", follow_redirects=True)
    with client.application.app_context():
        assert db.session.get(Application, app_id).status == "cancelled"


def test_delete_file(client, user):
    """Видалення файлу із заявки."""
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    data = {"title": "File Del", "short_description": "Desc", "files": (io.BytesIO(b"x"), "del.txt")}
    client.post("/applications/new", data=data, content_type='multipart/form-data', follow_redirects=True)

    with client.application.app_context():
        app_obj = get_app_by_title("File Del")
        file_id = app_obj.files[0].id

    response = client.post(f"/applications/file/{file_id}/delete", follow_redirects=True)
    assert "Файл видалено" in response.get_data(as_text=True)

    with client.application.app_context():
        assert db.session.get(ApplicationFile, file_id) is None


def test_access_denied_to_other_users(client, user):
    """Користувач не може бачити чужі заявки."""
    with client.application.app_context():
        other = User(email="other@example.com", role="applicant")
        other.set_password("12345678")
        db.session.add(other)
        db.session.commit()

        other_app = Application(title="Secret", short_description="...", owner_id=other.id)
        db.session.add(other_app)
        db.session.commit()
        app_id = other_app.id

    client.post("/login", data={"email": user.email, "password": "StrongPass1"})

    response = client.get(f"/applications/{app_id}", follow_redirects=True)
    assert "Ви не маєте доступу" in response.get_data(as_text=True)