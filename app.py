from flask import Flask, g
from extensions import db
from helpers import get_current_user

# Імпорти модулів маршрутів
import auth_routes
import application_routes
import expert_routes

# -----------------------
# Налаштування застосунку
# -----------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -----------------------
# Реєстрація маршрутів
# -----------------------
auth_routes.register_routes(app)
application_routes.register_routes(app)
expert_routes.register_routes(app)


# -----------------------
# Глобальний хук
# -----------------------
@app.before_request
def load_logged_in_user():
    g.user = get_current_user()


# -----------------------
# CLI команди
# -----------------------

@app.cli.command("init-db")
def init_db_command():
    from models import User, PasswordResetToken, Application
    with app.app_context():
        db.create_all()
    print("Базу даних ініціалізовано.")


# python -m flask create-expert
@app.cli.command("create-expert")
def create_expert_command():
    """Створює користувача-експерта (email: expert@test.com, pass: expert123)."""
    from models import User
    with app.app_context():
        email = "expert123@test.com"
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"Експерт {email} вже існує.")
            return

        u = User(email=email, role="expert")
        u.set_password("expert12345")
        db.session.add(u)
        db.session.commit()
        print(f"Створено експерта: {email} / expert123")


if __name__ == "__main__":
    from models import User, PasswordResetToken, Application

    with app.app_context():
        db.create_all()
    app.run(debug=True)