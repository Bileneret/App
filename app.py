from flask import Flask, g
from extensions import db
from helpers import get_current_user

# Імпорти модулів маршрутів (вони тепер безпечні)
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

# Ініціалізація БД
db.init_app(app)

# -----------------------
# Реєстрація маршрутів
# -----------------------
# Передаємо об'єкт app у функції, щоб маршрути прив'язалися до нього
auth_routes.register_routes(app)
application_routes.register_routes(app)

# -----------------------
# Глобальний хук перед запитом
# -----------------------

@app.before_request
def load_logged_in_user():
    """Перед кожним запитом встановлюємо g.user."""
    g.user = get_current_user()

# -----------------------
# CLI команда init-db
# -----------------------

@app.cli.command("init-db")
def init_db_command():
    """flask init-db — створити таблиці у БД."""
    # Імпорт моделей всередині функції, щоб переконатися, що вони зареєстровані
    from models import User, PasswordResetToken, Application
    with app.app_context():
        db.create_all()
    print("Базу даних ініціалізовано.")

if __name__ == "__main__":
    from models import User, PasswordResetToken, Application
    with app.app_context():
        db.create_all()
    app.run(debug=True)