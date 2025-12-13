import io
import os
from unittest.mock import patch
from extensions import db
from models import Application


def test_create_application_success(client, auth_headers, app):
    """Перевірка створення заявки (має стати Draft)."""
    data = {
        "title": "Тестова заявка",
        "short_description": "Опис винаходу",
        "files": (io.BytesIO(b"file content"), 'test.txt')
    }
    response = client.post(
        "/applications/new",
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers,
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Заявку успішно створено" in response.get_data(as_text=True)

    with app.app_context():
        app_db = Application.query.filter_by(title="Тестова заявка").first()
        assert app_db is not None
        assert app_db.status == "draft"
        assert len(app_db.files) == 1


def test_edit_application(client, auth_headers, app):
    """Тест редагування заявки."""
    # Спочатку створюємо заявку
    client.post("/applications/new", data={"title": "Old", "short_description": "Desc"}, headers=auth_headers)

    with app.app_context():
        app_id = Application.query.filter_by(title="Old").first().id

    # Редагуємо
    response = client.post(f"/applications/{app_id}/edit", data={
        "title": "New Title",
        "short_description": "New Desc"
    }, headers=auth_headers, follow_redirects=True)

    assert response.status_code == 200
    assert "Заявку оновлено" in response.get_data(as_text=True)


def test_submit_and_cancel_application(client, auth_headers, app):
    """Перевірка подачі та скасування заявки."""
    client.post("/applications/new", data={"title": "Submit App", "short_description": "Desc"}, headers=auth_headers)

    with app.app_context():
        app_id = Application.query.filter_by(title="Submit App").first().id

    # Подача
    client.post(f"/applications/{app_id}/submit", headers=auth_headers, follow_redirects=True)
    with app.app_context():
        assert db.session.get(Application, app_id).status == "submitted"

    # Скасування
    client.post(f"/applications/{app_id}/cancel", headers=auth_headers, follow_redirects=True)
    with app.app_context():
        assert db.session.get(Application, app_id).status == "cancelled"


def test_delete_file_error(client, auth_headers, app):
    """Тест обробки помилки при видаленні файлу (коли файлу фізично немає)."""
    # Створюємо заявку з файлом
    data = {
        'title': 'App with file',
        'short_description': 'Desc',
        'files': (io.BytesIO(b"content"), 'to_delete.txt')
    }
    client.post('/applications/new', data=data, content_type='multipart/form-data', headers=auth_headers)

    # Знаходимо ID файлу
    with app.app_context():
        app_obj = Application.query.filter_by(title="App with file").first()
        file_id = app_obj.files[0].id

    # Імітуємо помилку ОС при видаленні
    with patch('os.remove', side_effect=OSError("Disk error")):
        response = client.post(f'/applications/file/{file_id}/delete', headers=auth_headers, follow_redirects=True)
        assert response.status_code == 200
        assert "Файл видалено" in response.get_data(as_text=True)


def test_download_missing_file(client, auth_headers):
    """Тест спроби завантажити неіснуючий файл."""
    response = client.get('/uploads/ghost_file.txt', headers=auth_headers)
    assert response.status_code == 404