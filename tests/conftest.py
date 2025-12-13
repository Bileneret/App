import os
import sys
import shutil
import tempfile
import pytest

# Додаємо кореневу папку проєкту в шляхи пошуку Python
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app as flask_app
from extensions import db
from models import User


@pytest.fixture
def app():
    """Створює екземпляр застосунку з тестовою конфігурацією."""
    # Створюємо тимчасову директорію для файлів
    test_upload_folder = tempfile.mkdtemp()

    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,  # Вимикаємо CSRF для тестів
        "UPLOAD_FOLDER": test_upload_folder
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

    # Видаляємо тимчасову папку після тестів
    shutil.rmtree(test_upload_folder)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def user(app):
    """Створює звичайного користувача."""
    u = User(email="user@test.com", role="applicant")
    u.set_password("StrongPass1")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def expert(app):
    """Створює експерта."""
    u = User(email="expert@test.com", role="expert")
    u.set_password("ExpertPass1")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def admin(app):
    """Створює адміна."""
    u = User(email="admin@test.com", role="admin")
    u.set_password("AdminPass1")
    db.session.add(u)
    db.session.commit()
    return u