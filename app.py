from flask import Flask, g
from extensions import db  # ЗМІНЕНО: імпорт з extensions
from helpers import get_current_user
import auth_routes
import application_routes

# -----------------------
# Налаштування застосунку
# -----------------------

app = Flask(__name__)

# Секретний ключ
app.config["SECRET_KEY"] = "change-me-in-production"

# База даних
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Ініціалізація БД з додатком
db.init_app(app)  # ЗМІНЕНО: прив'язка до додатка тут

# -----------------------
# Глобальний хук перед запитом
# -----------------------

@app.before_request
def load_logged_in_user():
    """Перед кожним запитом встановлюємо g.user."""
    g.user = get_current_user()

# -----------------------
# Ініціалізація БД (CLI команда)
# -----------------------

@app.cli.command("init-db")
def init_db_command():
    """flask init-db — створити таблиці у БД."""
    from models import User, PasswordResetToken, Application
    with app.app_context():
        db.create_all()
    print("Базу даних ініціалізовано.")

# -----------------------
# Маршрути (Imports)
# -----------------------

if __name__ == "__main__":
    from models import User, PasswordResetToken, Application
    with app.app_context():
        db.create_all()
    app.run(debug=True)