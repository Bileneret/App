from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    g,
)

from extensions import db
from models import Application
from helpers import login_required


def register_routes(app):
    """Функція для реєстрації маршрутів заявок."""

    @app.route("/applications")
    @login_required
    def my_applications():
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
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            short_description = (request.form.get("short_description") or "").strip()

            errors = []
            if not title:
                errors.append("Назва є обов'язковою.")
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
        app_obj = Application.query.get_or_404(application_id)

        if app_obj.owner_id != g.user.id:
            flash("Ви не маєте доступу до цієї заявки.", "danger")
            return redirect(url_for("my_applications"))

        return render_template("application_detail.html", application=app_obj)

    @app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_application(application_id):
        app_obj = Application.query.get_or_404(application_id)

        if app_obj.owner_id != g.user.id:
            flash("Ви не можете редагувати цю заявку.", "danger")
            return redirect(url_for("my_applications"))

        # ВИПРАВЛЕННЯ: Дозволяємо редагувати також 'needs_changes'
        if app_obj.status not in ("draft", "needs_changes"):
            flash("Редагувати можна лише чернетки або заявки на доопрацюванні.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            short_description = (request.form.get("short_description") or "").strip()

            errors = []
            if not title:
                errors.append("Назва є обов'язковою.")
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
        app_obj = Application.query.get_or_404(application_id)

        if app_obj.owner_id != g.user.id:
            flash("Ви не можете подати цю заявку.", "danger")
            return redirect(url_for("my_applications"))

        # ВИПРАВЛЕННЯ: Дозволяємо подавати також 'needs_changes'
        if app_obj.status not in ("draft", "needs_changes"):
            flash("Подати можна лише чернетку або заявку на доопрацюванні.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        if not app_obj.title or not app_obj.short_description:
            flash("Неможливо подати заявку з порожніми полями. Відредагуйте її.", "danger")
            return redirect(url_for("edit_application", application_id=application_id))

        app_obj.status = "submitted"
        # Можна очистити коментар експерта при повторній подачі, щоб не плутати
        # app_obj.expert_comment = None

        db.session.commit()

        flash("Заявку подано на розгляд.", "success")
        return redirect(url_for("view_application", application_id=application_id))

    @app.route("/applications/<int:application_id>/cancel", methods=["POST"])
    @login_required
    def cancel_application(application_id):
        app_obj = Application.query.get_or_404(application_id)

        if app_obj.owner_id != g.user.id:
            flash("Ви не можете скасовувати чужу заявку.", "danger")
            return redirect(url_for("my_applications"))

        if app_obj.status not in ("submitted",):
            flash("Цю заявку неможливо скасувати на поточному етапі.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        app_obj.status = "cancelled"
        db.session.commit()

        flash("Заявку було успішно скасовано.", "success")
        return redirect(url_for("view_application", application_id=application_id))