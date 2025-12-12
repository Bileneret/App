from flask import render_template, request, redirect, url_for, flash, g
from sqlalchemy import func
from extensions import db
from models import User, Application
from helpers import admin_required


def register_routes(app):
    @app.route("/admin/users")
    @admin_required
    def admin_users():
        """Список всіх користувачів для керування."""
        users = User.query.order_by(User.id.asc()).all()
        return render_template("admin_users.html", users=users)

    @app.route("/admin/users/<int:user_id>/update", methods=["POST"])
    @admin_required
    def admin_update_user(user_id):
        """Зміна ролі або статусу блокування з урахуванням прав доступу."""
        # ВИПРАВЛЕНО: Новий синтаксис SQLAlchemy
        target_user = db.get_or_404(User, user_id)
        current_user = g.user

        # Захист: не можна редагувати самого себе
        if target_user.id == current_user.id:
            flash("Ви не можете змінювати власний акаунт.", "warning")
            return redirect(url_for("admin_users"))

        action = request.form.get("action")

        # --- ЛОГІКА ОБМЕЖЕНЬ ---

        # Якщо дію виконує звичайний адмін (не супер-адмін)
        if current_user.role == 'admin':
            # 1. Не можна чіпати інших адмінів або супер-адмінів
            if target_user.role in ['admin', 'super_admin']:
                flash("Звичайний адміністратор не може редагувати інших адміністраторів.", "danger")
                return redirect(url_for("admin_users"))

        if action == "change_role":
            new_role = request.form.get("role")

            # Валідація ролей
            if new_role not in ['applicant', 'expert', 'admin']:
                flash("Невірна роль.", "danger")
                return redirect(url_for("admin_users"))

            # Якщо звичайний адмін намагається призначити роль "admin"
            if current_user.role == 'admin' and new_role == 'admin':
                flash("Звичайний адміністратор не може призначати роль Адміністратора.", "danger")
                return redirect(url_for("admin_users"))

            target_user.role = new_role
            db.session.commit()
            flash(f"Роль користувача {target_user.email} змінено на {new_role}.", "success")

        elif action == "toggle_block":
            # Звичайний адмін не може банити адмінів
            if current_user.role == 'admin' and target_user.role in ['admin', 'super_admin']:
                flash("Ви не можете заблокувати цього користувача.", "danger")
                return redirect(url_for("admin_users"))

            target_user.is_blocked = not target_user.is_blocked
            db.session.commit()
            status = "заблоковано" if target_user.is_blocked else "розблоковано"
            flash(f"Користувача {target_user.email} {status}.", "success")

        return redirect(url_for("admin_users"))

    @app.route("/admin/stats")
    @admin_required
    def admin_stats():
        """Сторінка статистики."""
        # Підрахунок кількості заявок по кожному статусу
        stats_query = (
            db.session.query(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )

        # Перетворюємо в словник
        stats = {status: count for status, count in stats_query}

        # Прибираємо чернетки зі статистики
        if 'draft' in stats:
            del stats['draft']

        total_users = User.query.count()
        # Рахуємо загальну кількість заявок БЕЗ чернеток
        total_apps = Application.query.filter(Application.status != 'draft').count()

        return render_template("admin_stats.html", stats=stats, total_users=total_users, total_apps=total_apps)