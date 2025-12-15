import os
from flask import Flask, g, render_template, flash, redirect, url_for
from extensions import db, mail
from helpers import get_current_user

# Імпорти модулів маршрутів
import auth_routes
import application_routes
import expert_routes
import admin_routes

# -----------------------
# Налаштування застосунку
# -----------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- НАЛАШТУВАННЯ ПОШТИ (SMTP) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# Ваші реальні дані для входу
app.config['MAIL_USERNAME'] = 'copyregsystem@gmail.com'
app.config['MAIL_PASSWORD'] = 'qmog ycrm pvnc stvr'

# Від кого будуть приходити листи
app.config['MAIL_DEFAULT_SENDER'] = 'copyregsystem@gmail.com'

# Налаштування завантаження файлів
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ініціалізація розширень
db.init_app(app)
mail.init_app(app)

# -----------------------
# Обробка помилок
# -----------------------
@app.errorhandler(413)
def request_entity_too_large(error):
    """Обробка помилки, коли файли занадто великі."""
    flash("Загальний розмір файлів занадто великий! Спробуйте завантажити менше файлів.", "danger")
    return redirect(url_for('my_applications'))

# -----------------------
# Реєстрація маршрутів
# -----------------------
auth_routes.register_routes(app)
application_routes.register_routes(app)
expert_routes.register_routes(app)
admin_routes.register_routes(app)


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
    from models import User, PasswordResetToken, Application, ApplicationFile
    with app.app_context():
        db.create_all()
    print("Базу даних ініціалізовано.")


@app.cli.command("create-expert")
def create_expert_command():
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
    from models import User
    with app.app_context():
        email = "admin@test.com"
        if not User.query.filter_by(email=email).first():
            u = User(email=email, role="admin")
            u.set_password("admin123")
            db.session.add(u)
            db.session.commit()
            print(f"Створено звичайного адміна: {email}")
        else:
            print("Адмін вже існує")

@app.cli.command("create-super-admin")
def create_super_admin_command():
    from models import User
    with app.app_context():
        email = "super@test.com"
        if not User.query.filter_by(email=email).first():
            u = User(email=email, role="super_admin")
            u.set_password("super123")
            db.session.add(u)
            db.session.commit()
            print(f"Створено ГОЛОВНОГО адміна: {email}")
        else:
            print("Головний адмін вже існує")


if __name__ == "__main__":
    from models import User, PasswordResetToken, Application
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)