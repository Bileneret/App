import secrets
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    g,
)
from markupsafe import Markup  # Для форматування списку помилок
from email_validator import validate_email, EmailNotValidError

from extensions import db
from models import User, PasswordResetToken
from helpers import login_required, send_password_reset_email


def register_routes(app):
    """Функція для реєстрації маршрутів авторизації."""

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip()
            password = request.form.get("password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            # --- 1. Виконуємо всі перевірки (збираємо статус) ---

            # Перевірка валідності E-mail
            email_error_text = None
            normalized_email = email  # За замовчуванням залишаємо те, що ввів юзер

            try:
                valid = validate_email(email)
                normalized_email = valid.email
            except EmailNotValidError as e:
                msg = str(e)
                # Переклад специфічної помилки домену
                # Початкове: "The domain name test.com does not accept email"
                # Очікуване: "Домен test.com не приймає електронну пошту"
                if "The domain name" in msg and "does not accept email" in msg:
                    msg = msg.replace("The domain name", "Домен")
                    msg = msg.replace("does not accept email", "не приймає електронну пошту")

                # Додатковий переклад для "does not exist" (часта помилка)
                if "The domain name" in msg and "does not exist" in msg:
                    msg = msg.replace("The domain name", "Домен")
                    msg = msg.replace("does not exist", "не існує")

                email_error_text = f"Некоректний e-mail: {msg}"

            # Перевірка на існування користувача в БД
            # Використовуємо normalized_email, якщо валідація пройшла успішно,
            # або оригінальний email, якщо валідація впала (щоб все одно перевірити базу)
            existing_user = User.query.filter_by(email=normalized_email).first()
            is_exists = (existing_user is not None)

            # Перевірки пароля
            is_length_bad = len(password) < 8
            is_mismatch = password != confirm_password

            # --- 2. Формуємо список помилок за ПРІОРИТЕТОМ ---
            error_messages = []

            # Пріорітет 1: Користувач вже існує
            if is_exists:
                error_messages.append("Користувач з таким e-mail уже зареєстрований.")

            # Пріорітет 2: Довжина пароля
            if is_length_bad:
                error_messages.append("Пароль має містити щонайменше 8 символів.")

            # Пріорітет 3: Співпадіння паролів
            if is_mismatch:
                error_messages.append("Паролі не співпадають.")

            # Пріорітет 4: Некоректний email
            if email_error_text:
                error_messages.append(email_error_text)

            # --- 3. Якщо є помилки — виводимо одним повідомленням ---
            if error_messages:
                formatted_errors = []
                for i, msg in enumerate(error_messages):
                    formatted_errors.append(f"{i + 1}. {msg}")

                final_html_msg = "<br>".join(formatted_errors)

                flash(Markup(final_html_msg), "danger")
                return render_template("register.html", email=email)

            # --- 4. Якщо помилок немає — реєструємо ---
            user = User(email=normalized_email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash("Реєстрація успішна. Тепер увійдіть у систему.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip()
            password = request.form.get("password") or ""

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                # ПЕРЕВІРКА БЛОКУВАННЯ
                if user.is_blocked:
                    flash("Ваш акаунт заблоковано адміністратором.", "danger")
                    return render_template("login.html", email=email)

                session.clear()
                session["user_id"] = user.id
                flash("Ви успішно увійшли в систему.", "success")
                next_url = request.args.get("next")

                # Якщо це адмін, перенаправляємо одразу в адмінку
                if user.role == 'admin':
                    return redirect(url_for('admin_users'))

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
        return render_template("profile.html", user=g.user)

    @app.route("/password/reset/request", methods=["GET", "POST"])
    def request_password_reset():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip()

            if not email:
                flash("Введіть e-mail.", "danger")
                return render_template("request_password_reset.html")

            user = User.query.filter_by(email=email).first()

            if not user:
                flash(
                    "Якщо користувач з таким e-mail існує, на нього надіслано посилання.",
                    "info",
                )
                return redirect(url_for("login"))

            token_value = secrets.token_urlsafe(32)

            reset_token = PasswordResetToken(
                token=token_value,
                user=user,
            )
            db.session.add(reset_token)
            db.session.commit()

            reset_link = url_for("reset_password", token=token_value, _external=True)
            send_password_reset_email(user.email, reset_link)

            flash(
                "Якщо користувач з таким e-mail існує, на нього надіслано посилання.",
                "info",
            )
            return redirect(url_for("login"))

        return render_template("request_password_reset.html")

    @app.route("/password/reset/<token>", methods=["GET", "POST"])
    def reset_password(token):
        reset_token = PasswordResetToken.query.filter_by(token=token).first()

        if reset_token is None or reset_token.used or reset_token.is_expired:
            flash("Посилання для відновлення пароля недійсне або прострочене.", "danger")
            return redirect(url_for("login"))

        if request.method == "POST":
            new_password = request.form.get("password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            errors = []
            if len(new_password) < 8:
                errors.append("Пароль має містити щонайменше 8 символів.")
            if new_password != confirm_password:
                errors.append("Паролі не співпадають.")

            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template("reset_password.html", token=token)

            user = reset_token.user
            user.set_password(new_password)
            reset_token.used = True
            db.session.commit()

            flash("Пароль успішно змінено. Тепер увійдіть у систему.", "success")
            return redirect(url_for("login"))

        return render_template("reset_password.html", token=token)

    @app.route("/profile/password", methods=["GET", "POST"])
    @login_required
    def change_password():
        if request.method == "POST":
            # Беремо "current_password" як в HTML
            current_password = request.form.get("current_password") or ""
            new_password = request.form.get("new_password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            # 1. Збираємо результати перевірок
            is_length_bad = len(new_password) < 8
            is_mismatch = new_password != confirm_password
            is_old_wrong = not g.user.check_password(current_password)

            # 2. Формуємо список повідомлень за ПРІОРИТЕТОМ
            error_messages = []

            # Пріорітет 1: Довжина пароля
            if is_length_bad:
                error_messages.append("Пароль має містити щонайменше 8 символів.")

            # Пріорітет 2: Співпадіння паролів
            if is_mismatch:
                error_messages.append("Нові паролі не співпадають.")

            # Пріорітет 3: Перевірка поточного пароля
            if is_old_wrong:
                error_messages.append("Неправильний поточний пароль.")

            # 3. Вивід помилок
            if error_messages:
                formatted_errors = []
                for i, msg in enumerate(error_messages):
                    formatted_errors.append(f"{i + 1}. {msg}")

                final_html_msg = "<br>".join(formatted_errors)
                flash(Markup(final_html_msg), "danger")
                return render_template("change_password.html")

            # Успіх
            g.user.set_password(new_password)
            db.session.commit()

            flash("Пароль успішно змінено.", "success")
            return redirect(url_for("profile"))

        return render_template("change_password.html")