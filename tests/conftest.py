import os
import sys
import shutil
import pytest

# Додаємо кореневу папку проєкту в шляхи пошуку Python
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app as flask_app
from extensions import db
from models import User


@pytest.fixture
def app(tmp_path):
    """Створює екземпляр застосунку з тестовою конфігурацією."""
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["WTF_CSRF_ENABLED"] = False  # Вимикаємо CSRF для тестів

    # Налаштування тимчасової папки для завантажень
    upload_folder = tmp_path / "uploads"
    upload_folder.mkdir()
    flask_app.config['UPLOAD_FOLDER'] = str(upload_folder)

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    """Створює звичайного користувача."""
    u = User(email="user@example.com", role="applicant")
    u.set_password("StrongPass1")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def admin(app):
    """Створює адміна."""
    u = User(email="admin@test.com", role="admin")
    u.set_password("admin123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def expert(app):
    """Створює експерта."""
    u = User(email="expert@test.com", role="expert")
    u.set_password("expert123")
    db.session.add(u)
    db.session.commit()
    return u