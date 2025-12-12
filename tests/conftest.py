import os
import sys
import pytest

# Додаємо кореневу папку проєкту в шляхи пошуку Python
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- ІМПОРТИ ---
from app import app as flask_app
from extensions import db
from models import User, Application, PasswordResetToken


# ---------------------------


@pytest.fixture
def app():
    """Створює екземпляр застосунку з тестовою конфігурацією."""
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with flask_app.app_context():
        db.create_all()  # Створюємо таблиці
        yield flask_app
        db.session.remove()
        db.drop_all()  # Очищаємо після тесту


@pytest.fixture
def client(app):
    """Тестовий клієнт для виконання запитів."""
    return app.test_client()


@pytest.fixture
def user(app):
    """Створює тестового користувача в базі."""
    u = User(email="user@example.com")
    u.set_password("StrongPass1")
    db.session.add(u)
    db.session.commit()
    return u


# --- HOOKS FOR HTML REPORT (Налаштування звіту) ---

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # Беремо документацію (docstring) функції як опис
    docstring = getattr(item.function, "__doc__", None)
    report.description = str(docstring) if docstring else ""


def pytest_html_results_table_header(cells):
    # Додаємо колонку "Description" після колонки "Result"
    cells.insert(1, "<th>Description</th>")


def pytest_html_results_table_row(report, cells):
    # Заповнюємо колонку описом
    cells.insert(1, f"<td>{report.description}</td>")