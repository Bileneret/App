from flask import render_template, request, redirect, url_for, flash
from extensions import db
from models import Application
from helpers import expert_required


def register_routes(app):
    @app.route("/expert/applications")
    @expert_required
    def expert_dashboard():
        """Список заявок, поданих на розгляд (submitted)."""
        apps = (
            Application.query
            .filter(Application.status == 'submitted')
            .order_by(Application.created_at.asc())
            .all()
        )
        return render_template("expert_dashboard.html", applications=apps)

    @app.route("/expert/applications/<int:application_id>", methods=["GET", "POST"])
    @expert_required
    def expert_review(application_id):
        """Сторінка розгляду конкретної заявки."""
        app_obj = Application.query.get_or_404(application_id)

        if request.method == "POST":
            decision = request.form.get("decision")  # approved, rejected, needs_changes
            comment = (request.form.get("comment") or "").strip()

            if decision not in ["approved", "rejected", "needs_changes"]:
                flash("Невірний статус рішення.", "danger")
                return redirect(url_for("expert_review", application_id=app_obj.id))

            # Якщо відхиляємо або відправляємо на доопрацювання - коментар обов'язковий
            if decision in ["rejected", "needs_changes"] and not comment:
                flash("Для цього рішення коментар є обов'язковим!", "danger")
                return render_template("expert_review.html", application=app_obj)

            app_obj.status = decision
            app_obj.expert_comment = comment
            app_obj.updated_at = db.func.now()

            db.session.commit()

            flash(f"Заявку переведено у статус: {decision}", "success")
            return redirect(url_for("expert_dashboard"))

        return render_template("expert_review.html", application=app_obj)