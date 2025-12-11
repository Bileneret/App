import secrets
from datetime import datetime

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    g,
)

from email_validator import validate_email, EmailNotValidError

from app import app, db
from models import User, PasswordResetToken
from helpers import login_required, send_password_reset_email


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

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
            errors.append("Користувач з таким e-mail уже зареєстрований.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", email=email)

        user = User(email=email)
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
    Запит на відновлення пароля:
      - користувач вводить e-mail,
      - якщо користувач існує — генеруємо токен, зберігаємо,
      - формуємо посилання і "надсилаємо" (print),
      - завжди показуємо нейтральне повідомлення.
    """
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()

        if not email:
            flash("Введіть e-mail.", "danger")
            return render_template("request_password_reset.html")

        user = User.query.filter_by(email=email).first()

        # Не розкриваємо, чи є такий користувач
        if not user:
            flash(
                "Якщо користувач з таким e-mail існує, на нього надіслано посилання для відновлення пароля.",
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

        reset_link = url_for("reset_password", token=token_value, _external=True)
        send_password_reset_email(user.email, reset_link)

        flash(
            "Якщо користувач з таким e-mail існує, на нього надіслано посилання для відновлення пароля.",
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
        old_password = request.form.get("old_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not g.user.check_password(old_password):
            flash("Неправильний поточний пароль.", "danger")
            return render_template("change_password.html")

        if len(new_password) < 8:
            flash("Новий пароль має містити щонайменше 8 символів.", "danger")
            return render_template("change_password.html")

        if new_password != confirm_password:
            flash("Новий пароль і підтвердження не співпадають.", "danger")
            return render_template("change_password.html")

        g.user.set_password(new_password)
        db.session.commit()

        flash("Пароль успішно змінено.", "success")
        return redirect(url_for("profile"))

    return render_template("change_password.html")