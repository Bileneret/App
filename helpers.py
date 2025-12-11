from functools import wraps

from flask import session, g, flash, redirect, request, url_for

from models import User


def send_password_reset_email(to_email: str, reset_link: str):
    # Тут у тебе в оригіналі був просто print — залишаю так само.
    print("=== ЛИСТ ДЛЯ ВІДНОВЛЕННЯ ПАРОЛЯ ===")
    print(f"Кому: {to_email}")
    print(f"Посилання: {reset_link}")
    print("====================================")
    return


def get_current_user():
    """Повертає поточного користувача або None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(view_func):
    """Простий декоратор для захисту сторінок, де потрібен логін."""

    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(**kwargs)

    return wrapped_view