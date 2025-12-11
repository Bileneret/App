from datetime import datetime
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy

# -----------------------
# Налаштування застосунку
# -----------------------

app = Flask(__name__)

# Секретний ключ для сесій і flash-повідомлень
app.config["SECRET_KEY"] = "change-me-in-production"

# SQLite база даних у файлі app.db
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Імпортуємо моделі, щоб вони були зареєстровані в SQLAlchemy
from models import User, PasswordResetToken, Application  # noqa: E402,F401

# Допоміжні функції (get_current_user, тощо)
from helpers import get_current_user  # noqa: E402

# -----------------------
# Глобальний хук перед запитом
# -----------------------

@app.before_request
def load_logged_in_user():
    """Перед кожним запитом встановлюємо g.user."""
    g.user = get_current_user()

# -----------------------
# Маршрути
# -----------------------
# ВАЖЛИВО: просто імпортуючи ці модулі,
# ми реєструємо всі @app.route(...) з них.
import auth_routes  # noqa: E402,F401
import application_routes  # noqa: E402,F401

# -----------------------
# Ініціалізація БД
# -----------------------

@app.cli.command("init-db")
def init_db_command():
    """flask init-db — створити таблиці у БД."""
    with app.app_context():
        db.create_all()
    print("Базу даних ініціалізовано.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)