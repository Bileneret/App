import os
import sys
import pytest

# Додаємо корінь проекту в шляхи, щоб бачити app.py
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app as flask_app
from extensions import db
from models import User


@pytest.fixture
def app():
    """Створює екземпляр додатку для тестів."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SERVER_NAME": "localhost.localdomain"
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Тестовий клієнт (браузер)."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI-ранер для команд терміналу."""
    return app.test_cli_runner()


# --- ФІКСТУРИ КОРИСТУВАЧІВ (ОБ'ЄКТИ) ---

@pytest.fixture
def user(app):
    """Створює і повертає об'єкт звичайного користувача."""
    with app.app_context():
        u = User(email="user@test.com", role="applicant")
        u.set_password("password")
        db.session.add(u)
        db.session.commit()
        # Повертаємо об'єкт, прив'язаний до сесії (або ID)
        return u


@pytest.fixture
def expert(app):
    """Створює і повертає об'єкт експерта."""
    with app.app_context():
        u = User(email="expert@test.com", role="expert")
        u.set_password("password")
        db.session.add(u)
        db.session.commit()
        return u


@pytest.fixture
def admin(app):
    """Створює і повертає об'єкт адміна."""
    with app.app_context():
        u = User(email="admin@test.com", role="admin")
        u.set_password("password")
        db.session.add(u)
        db.session.commit()
        return u


# --- ФІКСТУРИ АВТОРИЗАЦІЇ (HEADERS/COOKIES) ---

@pytest.fixture
def auth_headers(client, app):
    """Авторизує звичайного користувача (applicant)."""
    with app.app_context():
        if not User.query.filter_by(email="auth_user@test.com").first():
            u = User(email="auth_user@test.com", role="applicant")
            u.set_password("password")
            db.session.add(u)
            db.session.commit()

    client.post('/login', data={'email': 'auth_user@test.com', 'password': 'password'}, follow_redirects=True)
    return {}


@pytest.fixture
def expert_headers(client, app):
    """Авторизує експерта."""
    with app.app_context():
        if not User.query.filter_by(email="expert_h@test.com").first():
            u = User(email="expert_h@test.com", role="expert")
            u.set_password("password")
            db.session.add(u)
            db.session.commit()

    client.post('/login', data={'email': 'expert_h@test.com', 'password': 'password'}, follow_redirects=True)
    return {}


@pytest.fixture
def admin_headers(client, app):
    """Авторизує адміна."""
    with app.app_context():
        if not User.query.filter_by(email="admin_h@test.com").first():
            u = User(email="admin_h@test.com", role="admin")
            u.set_password("password")
            db.session.add(u)
            db.session.commit()

    client.post('/login', data={'email': 'admin_h@test.com', 'password': 'password'}, follow_redirects=True)
    return {}


# --- HOOKS ДЛЯ ЗВІТУ ---
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    docstring = getattr(item.function, "__doc__", None)
    report.description = str(docstring) if docstring else ""


def pytest_html_results_table_header(cells):
    cells.insert(1, "<th>Description</th>")


def pytest_html_results_table_row(report, cells):
    cells.insert(1, f"<td>{report.description}</td>")