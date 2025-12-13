import os
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    g,
    send_from_directory,
    abort
)
from werkzeug.utils import secure_filename

from extensions import db
from models import Application, ApplicationFile
from helpers import login_required


def register_routes(app):
    # Дозволяємо будь-які файли, що мають розширення
    def allowed_file(filename):
        return '.' in filename

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

            # --- ЛОГІКА ФАЙЛІВ ---
            files = request.files.getlist('files')
            valid_files = []

            for file in files:
                if file and file.filename and file.filename.strip() != "":
                    valid_files.append(file)

            messages = []

            # Перевірка ліміту
            if len(valid_files) > 10:
                count_before = len(valid_files)
                valid_files = valid_files[:10]
                messages.append(
                    f"⚠️ Ви обрали {count_before} файлів. Ліміт системи — 10. До заявки було збережено лише перші 10 файлів.")

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

            # Створення заявки
            app_obj = Application(
                title=title,
                short_description=short_description,
                owner_id=g.user.id,
                status="draft"
            )
            db.session.add(app_obj)
            db.session.flush()

            # Збереження
            for file in valid_files:
                original_filename = secure_filename(file.filename)
                unique_filename = f"app_{app_obj.id}_{original_filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

                new_file = ApplicationFile(filename=unique_filename, application_id=app_obj.id)
                db.session.add(new_file)

            db.session.commit()

            flash("Заявку успішно створено.", "success")
            for msg in messages:
                flash(msg, "warning")

            return redirect(url_for("view_application", application_id=app_obj.id))

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

        if app_obj.owner_id != g.user.id and g.user.role not in ('expert', 'admin', 'super_admin'):
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

        if app_obj.status not in ("draft", "needs_changes"):
            flash("Редагувати можна лише чернетки або заявки на доопрацюванні.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            short_description = (request.form.get("short_description") or "").strip()

            errors = []
            if not title:
                errors.append("Назва є обов'язковою.")

            # --- ЛОГІКА ДОДАВАННЯ ФАЙЛІВ ---
            new_files = request.files.getlist('files')
            valid_new_files = []

            for file in new_files:
                if file and file.filename and file.filename.strip() != "":
                    valid_new_files.append(file)

            messages = []

            # Рахуємо місце
            current_count = len(app_obj.files)
            available_slots = 10 - current_count

            if len(valid_new_files) > available_slots:
                extra_files = len(valid_new_files) - available_slots
                valid_new_files = valid_new_files[:available_slots]
                if available_slots == 0:
                    messages.append("⚠️ Ви досягли ліміту 10 файлів. Нові файли не було додано.")
                else:
                    messages.append(
                        f"⚠️ Ви намагалися додати більше файлів, ніж дозволено. Було додано лише {available_slots}, а {extra_files} відхилено.")

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

            # Збереження
            for file in valid_new_files:
                original_filename = secure_filename(file.filename)
                unique_filename = f"app_{app_obj.id}_{original_filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

                new_file_record = ApplicationFile(filename=unique_filename, application_id=app_obj.id)
                db.session.add(new_file_record)

            db.session.commit()

            flash("Заявку оновлено.", "success")
            for msg in messages:
                flash(msg, "warning")

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

        if app_obj.status not in ("draft", "needs_changes"):
            flash("Подати можна лише чернетку або заявку на доопрацюванні.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        if not app_obj.title or not app_obj.short_description:
            flash("Неможливо подати заявку з порожніми полями.", "danger")
            return redirect(url_for("edit_application", application_id=application_id))

        app_obj.status = "submitted"
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

    @app.route("/applications/file/<int:file_id>/delete", methods=["POST"])
    @login_required
    def delete_file_route(file_id):
        file_record = ApplicationFile.query.get_or_404(file_id)
        app_obj = file_record.application

        if app_obj.owner_id != g.user.id:
            flash("Ви не маєте права видаляти цей файл.", "danger")
            return redirect(url_for("my_applications"))

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_record.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

        db.session.delete(file_record)
        db.session.commit()

        flash("Файл видалено.", "success")
        return redirect(url_for("edit_application", application_id=app_obj.id))

    # --- СКАЧУВАННЯ ФАЙЛІВ (ПУБЛІЧНИЙ ДОСТУП ДЛЯ GOOGLE) ---
    @app.route("/uploads/<filename>")
    # @login_required  <-- ВИМКНЕНО ДЛЯ GOOGLE DOCS VIEWER
    def download_file(filename):
        # Перевірка на існування
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            return abort(404)

        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)