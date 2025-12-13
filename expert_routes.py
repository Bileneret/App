from flask import render_template, request, redirect, url_for, flash, g
from extensions import db
from models import Application
from helpers import expert_required, send_status_update_email  # <--- Імпорт функції


def register_routes(app):
    @app.route("/expert/applications")
    @expert_required
    def expert_dashboard():
        apps = (
            Application.query
            .filter(Application.status == 'submitted')
            .filter(Application.owner_id != g.user.id)
            .order_by(Application.created_at.asc())
            .all()
        )
        return render_template("expert_dashboard.html", applications=apps)

    @app.route("/expert/applications/<int:application_id>", methods=["GET", "POST"])
    @expert_required
    def expert_review(application_id):
        app_obj = db.get_or_404(Application, application_id)

        if app_obj.owner_id == g.user.id:
            flash("Ви не можете оцінювати власні заявки.", "danger")
            return redirect(url_for("expert_dashboard"))

        if request.method == "POST":
            decision = request.form.get("decision")
            comment = (request.form.get("comment") or "").strip()

            if decision not in ["approved", "rejected", "needs_changes"]:
                flash("Невірний статус рішення.", "danger")
                return redirect(url_for("expert_review", application_id=app_obj.id))

            if decision in ["rejected", "needs_changes"] and not comment:
                flash("Для цього рішення коментар є обов'язковим!", "danger")
                return render_template("expert_review.html", application=app_obj)

            # Оновлюємо статус
            app_obj.status = decision
            app_obj.expert_comment = comment

            db.session.commit()

            # --- ВІДПРАВКА ЛИСТА ---
            send_status_update_email(app_obj)
            # -----------------------

            flash(f"Заявку переведено у статус: {decision}. Користувача сповіщено.", "success")
            return redirect(url_for("expert_dashboard"))

        return render_template("expert_review.html", application=app_obj)