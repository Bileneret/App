from functools import wraps
from flask import session, g, flash, redirect, request, url_for
from models import User


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


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(**kwargs)

    return wrapped_view


def expert_required(view_func):
    """Декоратор: доступ лише для експертів (і адмінів)."""
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))

        if g.user.role not in ['expert', 'admin']:
            flash("У вас немає прав доступу до цієї сторінки.", "danger")
            return redirect(url_for("index"))

        return view_func(**kwargs)

    return wrapped_view


def admin_required(view_func):
    """Декоратор: доступ лише для адмінів."""
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))

        if g.user.role != 'admin':
            flash("Доступ заборонено. Потрібні права адміністратора.", "danger")
            return redirect(url_for("index"))

        return view_func(**kwargs)

    return wrapped_view