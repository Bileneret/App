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
        """Зміна ролі або статусу блокування."""
        user = User.query.get_or_404(user_id)

        # Захист: не можна редагувати самого себе
        if user.id == g.user.id:
            flash("Ви не можете змінювати власний акаунт.", "warning")
            return redirect(url_for("admin_users"))

        action = request.form.get("action")

        if action == "change_role":
            new_role = request.form.get("role")
            if new_role in ['applicant', 'expert', 'admin']:
                user.role = new_role
                db.session.commit()
                flash(f"Роль користувача {user.email} змінено на {new_role}.", "success")
            else:
                flash("Невірна роль.", "danger")

        elif action == "toggle_block":
            user.is_blocked = not user.is_blocked
            db.session.commit()
            status = "заблоковано" if user.is_blocked else "розблоковано"
            flash(f"Користувача {user.email} {status}.", "success")

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

        # Перетворюємо в словник для зручності: {'draft': 5, 'approved': 2}
        stats = {status: count for status, count in stats_query}

        total_users = User.query.count()
        total_apps = Application.query.count()

        return render_template("admin_stats.html", stats=stats, total_users=total_users, total_apps=total_apps)