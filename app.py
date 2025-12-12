from flask import Flask, g
from extensions import db
from helpers import get_current_user

# Імпорти модулів маршрутів
import auth_routes
import application_routes
import expert_routes
import admin_routes  # <--- НОВИЙ МОДУЛЬ

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
admin_routes.register_routes(app)  # <--- РЕЄСТРАЦІЯ

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


@app.cli.command("create-expert")
def create_expert_command():
    """Створює користувача-експерта."""
    from models import User
    with app.app_context():
        email = "expert@test.com"
        if not User.query.filter_by(email=email).first():
            u = User(email=email, role="expert")
            u.set_password("expert123")
            db.session.add(u)
            db.session.commit()
            print(f"Створено експерта: {email}")
        else:
            print("Експерт вже існує")

@app.cli.command("create-admin")
def create_admin_command():
    """Створює адміністратора (admin@test.com / admin123)."""
    from models import User
    with app.app_context():
        email = "admin@test.com"
        if not User.query.filter_by(email=email).first():
            u = User(email=email, role="admin")
            u.set_password("admin123")
            db.session.add(u)
            db.session.commit()
            print(f"Створено адміна: {email}")
        else:
            print("Адмін вже існує")


if __name__ == "__main__":
    from models import User, PasswordResetToken, Application
    with app.app_context():
        db.create_all()
    app.run(debug=True)