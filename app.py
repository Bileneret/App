from datetime import datetime, timedelta
import secrets
import smtplib
from email.message import EmailMessage

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError

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


# -----------------------
# Моделі даних
# -----------------------

class User(db.Model):
    """Користувач системи."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="applicant")  # applicant / expert / admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class PasswordResetToken(db.Model):
    """Токен для відновлення пароля (спрощений варіант для навчального проєкту)."""
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)

    user = db.relationship("User")

    @property
    def is_expired(self) -> bool:
        # Токен діє 24 години
        return datetime.utcnow() > self.created_at + timedelta(hours=24)


class Application(db.Model):
    """Заявка на авторське свідоцтво."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    short_description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(50), nullable=False, default="draft")
    # Можливі значення:
    # draft         – чорнетка
    # submitted     – подано на розгляд
    # under_review  – на розгляді (епік 3)
    # needs_changes – потребує доопрацювання
    # rejected      – відхилено
    # approved      – схвалено
    # cancelled     – скасовано заявником

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", backref="applications")


# -----------------------
# Допоміжні функції
# -----------------------

def send_password_reset_email(to_email: str, reset_link: str):
    print("=== ЛИСТ ДЛЯ ВІДНОВЛЕННЯ ПАРОЛЯ ===")
    print(f"Кому: {to_email}")
    print(f"Посилання: {reset_link}")
    print("====================================")
    return


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


@app.before_request
def load_logged_in_user():
    """Перед кожним запитом встановлюємо g.user."""
    g.user = get_current_user()


def login_required(view_func):
    """Проста декоратор-функція для захисту сторінок, де потрібен логін."""
    from functools import wraps

    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(**kwargs)

    return wrapped_view


# -----------------------
# Маршрути (routes)
# -----------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        # Валідація полів
        errors = []

        # Перевірка e-mail
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            errors.append(f"Некоректний e-mail: {str(e)}")

        if len(password) < 8:
            errors.append("Пароль має містити щонайменше 8 символів.")
        if password != confirm_password:
            errors.append("Паролі не співпадають.")

        existing = User.query.filter_by(email=email).first()
        if existing:
            errors.append("Користувач з таким e-mail уже існує.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html", email=email)

        # Створення користувача
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Реєстрація успішна! Тепер увійдіть у систему.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            flash("Ви успішно увійшли в систему.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("profile"))
        else:
            flash("Невірний e-mail або пароль.", "danger")
            return render_template("login.html", email=email)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Ви вийшли із системи.", "info")
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile():
    """Сторінка профілю поточного користувача."""
    return render_template("profile.html", user=g.user)


@app.route("/password/reset/request", methods=["GET", "POST"])
def request_password_reset():
    """
    Запит на відновлення пароля.
    Користувач вводить e-mail, система:
      - знаходить користувача (якщо є),
      - генерує токен,
      - зберігає в таблиці PasswordResetToken,
      - формує посилання,
      - надсилає/виводить посилання,
      - показує користувачу нейтральне повідомлення.
    """
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()

        if not email:
            flash("Введіть e-mail.", "danger")
            return render_template("request_password_reset.html")

        # Шукаємо користувача
        user = User.query.filter_by(email=email).first()

        # НЕ розкриваємо, чи є такий користувач — безпекова практика
        if not user:
            flash(
                "Якщо користувач з таким e-mail існує, інструкції вже надіслані.",
                "info",
            )
            return redirect(url_for("login"))

        # Створюємо унікальний токен
        token_value = secrets.token_urlsafe(32)

        reset_token = PasswordResetToken(
            token=token_value,
            user=user,
        )
        db.session.add(reset_token)
        db.session.commit()

        # Формуємо лінк для відновлення
        reset_link = url_for("reset_password", token=token_value, _external=True)

        # Відправляємо / логимо
        send_password_reset_email(user.email, reset_link)

        # Повідомлення користувачу
        flash(
            "Якщо користувач з таким e-mail існує, на нього надіслано посилання для відновлення пароля.",
            "info",
        )
        return redirect(url_for("login"))

    # GET-запит — просто форма
    return render_template("request_password_reset.html")


@app.route("/password/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token).first()

    if reset_token is None or reset_token.used or reset_token.is_expired:
        flash("Токен відновлення пароля недійсний або прострочений.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if len(password) < 8:
            flash("Пароль має містити щонайменше 8 символів.", "danger")
            return render_template("reset_password.html")

        if password != confirm_password:
            flash("Паролі не співпадають.", "danger")
            return render_template("reset_password.html")

        user = reset_token.user
        user.set_password(password)
        reset_token.used = True
        db.session.commit()

        flash("Пароль успішно змінено. Увійдіть з новим паролем.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


@app.route("/profile/password", methods=["GET", "POST"])
@login_required
def change_password():
    """Зміна пароля авторизованого користувача."""
    if request.method == "POST":
        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        # Перевіряємо поточний пароль
        if not g.user.check_password(current_password):
            flash("Невірний поточний пароль.", "danger")
            return render_template("change_password.html")

        # Перевірка нового пароля
        if len(new_password) < 8:
            flash("Новий пароль має містити щонайменше 8 символів.", "danger")
            return render_template("change_password.html")

        if new_password != confirm_password:
            flash("Новий пароль і підтвердження не співпадають.", "danger")
            return render_template("change_password.html")

        # Оновлюємо пароль
        g.user.set_password(new_password)
        db.session.commit()

        flash("Пароль успішно змінено.", "success")
        return redirect(url_for("profile"))

    return render_template("change_password.html")


@app.route("/applications")
@login_required
def my_applications():
    """Список заявок поточного користувача."""
    apps = (
        Application.query
        .filter_by(owner_id=g.user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return render_template("applications_list.html", applications=apps)


@app.route("/applications/new", methods=["GET", "POST"])
@login_required
def create_application():
    """Створення нової заявки (чорнетка)."""
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        short_description = (request.form.get("short_description") or "").strip()

        errors = []
        if not title:
            errors.append("Назва заявки є обов'язковою.")
        if len(title) > 255:
            errors.append("Назва заявки не може перевищувати 255 символів.")
        if not short_description:
            errors.append("Короткий опис є обов'язковим.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "application_form.html",
                mode="create",
                application=None,
                title_value=title,
                description_value=short_description,
            )

        app_obj = Application(
            title=title,
            short_description=short_description,
            owner_id=g.user.id,
            status="draft",
        )
        db.session.add(app_obj)
        db.session.commit()

        flash("Заявку створено як чернетку.", "success")
        return redirect(url_for("my_applications"))

    return render_template(
        "application_form.html",
        mode="create",
        application=None,
        title_value="",
        description_value="",
    )


@app.route("/applications/<int:application_id>")
@login_required
def view_application(application_id):
    """Детальний перегляд заявки (тільки власник)."""
    app_obj = Application.query.get_or_404(application_id)

    if app_obj.owner_id != g.user.id and g.user.role not in ("expert", "admin"):
        flash("У вас немає доступу до цієї заявки.", "danger")
        return redirect(url_for("my_applications"))

    return render_template("application_detail.html", application=app_obj)


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
@login_required
def edit_application(application_id):
    """Редагування заявки, поки вона в статусі draft або needs_changes."""
    app_obj = Application.query.get_or_404(application_id)

    if app_obj.owner_id != g.user.id:
        flash("Ви не можете редагувати чужу заявку.", "danger")
        return redirect(url_for("my_applications"))

    if app_obj.status not in ("draft", "needs_changes"):
        flash("Редагування можливе лише для чернеток або заявок на доопрацюванні.", "warning")
        return redirect(url_for("view_application", application_id=application_id))

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        short_description = (request.form.get("short_description") or "").strip()

        errors = []
        if not title:
            errors.append("Назва заявки є обов'язковою.")
        if len(title) > 255:
            errors.append("Назва заявки не може перевищувати 255 символів.")
        if not short_description:
            errors.append("Короткий опис є обов'язковим.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "application_form.html",
                mode="edit",
                application=app_obj,
                title_value=title,
                description_value=short_description,
            )

        app_obj.title = title
        app_obj.short_description = short_description
        db.session.commit()

        flash("Заявку оновлено.", "success")
        return redirect(url_for("view_application", application_id=application_id))

    # GET запит
    return render_template(
        "application_form.html",
        mode="edit",
        application=app_obj,
        title_value=app_obj.title,
        description_value=app_obj.short_description,
    )


@app.route("/applications/<int:application_id>/submit", methods=["POST"])
@login_required
def submit_application(application_id):
    """Змінити статус заявки з draft/needs_changes на submitted."""
    app_obj = Application.query.get_or_404(application_id)

    if app_obj.owner_id != g.user.id:
        flash("Ви не можете подавати чужу заявку.", "danger")
        return redirect(url_for("my_applications"))

    if app_obj.status not in ("draft", "needs_changes"):
        flash("Цю заявку вже подано або опрацьовано.", "warning")
        return redirect(url_for("view_application", application_id=application_id))

    # Проста валідація: щоб не було порожніх полів
    if not app_obj.title or not app_obj.short_description:
        flash("Неможливо подати заявку з порожніми полями. Відредагуйте її.", "danger")
        return redirect(url_for("edit_application", application_id=application_id))

    app_obj.status = "submitted"
    db.session.commit()

    flash("Заявку подано на розгляд.", "success")
    return redirect(url_for("view_application", application_id=application_id))


@app.route("/applications/<int:application_id>/cancel", methods=["POST"])
@login_required
def cancel_application(application_id):
    """
    Скасування вже надісланої заявки (submitted або, за бажанням, under_review).
    Заявка помічається як cancelled, але не видаляється з бази.
    """
    app_obj = Application.query.get_or_404(application_id)

    if app_obj.owner_id != g.user.id:
        flash("Ви не можете скасовувати чужу заявку.", "danger")
        return redirect(url_for("my_applications"))

    # Дозволяємо скасування тільки якщо заявка ще "в процесі"
    if app_obj.status not in ("submitted",):
        # якщо хочеш, можеш дозволити і "under_review":
        # if app_obj.status not in ("submitted", "under_review"):
        flash("Цю заявку неможливо скасувати на поточному етапі.", "warning")
        return redirect(url_for("view_application", application_id=application_id))

    app_obj.status = "cancelled"
    db.session.commit()

    flash("Заявку було успішно скасовано.", "success")
    return redirect(url_for("view_application", application_id=application_id))


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
