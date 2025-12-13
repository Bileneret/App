import os
from flask import (
    render_template, request, redirect, url_for, flash, g, send_from_directory, abort
)
from werkzeug.utils import secure_filename
from extensions import db
from models import Application, ApplicationFile
from helpers import login_required, save_history


def register_routes(app):
    @app.route("/applications")
    @login_required
    def my_applications():
        # Новий синтаксис Select
        stmt = (
            db.select(Application)
            .filter_by(owner_id=g.user.id)
            .order_by(Application.created_at.desc())
        )
        apps = db.session.execute(stmt).scalars().all()
        return render_template("applications_list.html", applications=apps)

    @app.route("/applications/new", methods=["GET", "POST"])
    @login_required
    def create_application():
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            short_description = (request.form.get("short_description") or "").strip()

            errors = []
            if not title: errors.append("Назва є обов'язковою.")
            if not short_description: errors.append("Короткий опис є обов'язковим.")

            files = request.files.getlist('files')
            valid_files = [f for f in files if f and f.filename and f.filename.strip() != ""]

            messages = []
            if len(valid_files) > 10:
                count_before = len(valid_files)
                valid_files = valid_files[:10]
                messages.append(f"⚠️ Ви обрали {count_before} файлів. Збережено перші 10.")

            if errors:
                for e in errors: flash(e, "danger")
                return render_template("application_form.html", mode="create", application=None, title_value=title,
                                       description_value=short_description)

            app_obj = Application(
                title=title,
                short_description=short_description,
                owner_id=g.user.id,
                status="draft"
            )
            db.session.add(app_obj)
            db.session.flush()

            for file in valid_files:
                original_filename = secure_filename(file.filename)
                unique_filename = f"app_{app_obj.id}_{original_filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                new_file = ApplicationFile(filename=unique_filename, application_id=app_obj.id)
                db.session.add(new_file)

            # --- ІСТОРІЯ: Створено ---
            save_history(app_obj, g.user, "created")

            db.session.commit()

            flash("Заявку успішно створено.", "success")
            for msg in messages: flash(msg, "warning")
            return redirect(url_for("view_application", application_id=app_obj.id))

        return render_template("application_form.html", mode="create", application=None, title_value="",
                               description_value="")

    @app.route("/applications/<int:application_id>")
    @login_required
    def view_application(application_id):
        # ВИПРАВЛЕНО: db.get_or_404
        app_obj = db.get_or_404(Application, application_id)

        if app_obj.owner_id != g.user.id and g.user.role not in ('expert', 'admin', 'super_admin'):
            flash("Ви не маєте доступу до цієї заявки.", "danger")
            return redirect(url_for("my_applications"))
        return render_template("application_detail.html", application=app_obj)

    @app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_application(application_id):
        # ВИПРАВЛЕНО: db.get_or_404
        app_obj = db.get_or_404(Application, application_id)

        if app_obj.owner_id != g.user.id:
            flash("Ви не можете редагувати цю заявку.", "danger")
            return redirect(url_for("my_applications"))
        if app_obj.status not in ("draft", "needs_changes"):
            flash("Редагувати можна лише чернетку.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            short_description = (request.form.get("short_description") or "").strip()

            if not title:
                flash("Назва є обов'язковою.", "danger")
                return render_template("application_form.html", mode="edit", application=app_obj, title_value=title,
                                       description_value=short_description)

            new_files = request.files.getlist('files')
            valid_new_files = [f for f in new_files if f and f.filename and f.filename.strip() != ""]

            current_count = len(app_obj.files)
            available_slots = 10 - current_count
            messages = []

            if len(valid_new_files) > available_slots:
                valid_new_files = valid_new_files[:available_slots]
                messages.append(f"⚠️ Ліміт перевищено. Додано лише {available_slots} файлів.")

            app_obj.title = title
            app_obj.short_description = short_description

            for file in valid_new_files:
                original_filename = secure_filename(file.filename)
                unique_filename = f"app_{app_obj.id}_{original_filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                new_file_record = ApplicationFile(filename=unique_filename, application_id=app_obj.id)
                db.session.add(new_file_record)

            # --- ІСТОРІЯ: Відредаговано ---
            save_history(app_obj, g.user, "edited")

            db.session.commit()
            flash("Заявку оновлено.", "success")
            for msg in messages: flash(msg, "warning")
            return redirect(url_for("view_application", application_id=application_id))

        return render_template("application_form.html", mode="edit", application=app_obj, title_value=app_obj.title,
                               description_value=app_obj.short_description)

    @app.route("/applications/<int:application_id>/submit", methods=["POST"])
    @login_required
    def submit_application(application_id):
        # ВИПРАВЛЕНО: db.get_or_404
        app_obj = db.get_or_404(Application, application_id)

        if app_obj.owner_id != g.user.id:
            flash("Ви не можете подати цю заявку.", "danger")
            return redirect(url_for("my_applications"))
        if app_obj.status not in ("draft", "needs_changes"):
            flash("Подати можна лише чернетку.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        app_obj.status = "submitted"

        # --- ІСТОРІЯ: Подано на розгляд ---
        save_history(app_obj, g.user, "status_change")

        db.session.commit()
        flash("Заявку подано на розгляд.", "success")
        return redirect(url_for("view_application", application_id=application_id))

    @app.route("/applications/<int:application_id>/cancel", methods=["POST"])
    @login_required
    def cancel_application(application_id):
        # ВИПРАВЛЕНО: db.get_or_404
        app_obj = db.get_or_404(Application, application_id)

        if app_obj.owner_id != g.user.id:
            flash("Ви не можете скасовувати чужу заявку.", "danger")
            return redirect(url_for("my_applications"))
        if app_obj.status not in ("submitted",):
            flash("Цю заявку неможливо скасувати.", "warning")
            return redirect(url_for("view_application", application_id=application_id))

        app_obj.status = "cancelled"

        # --- ІСТОРІЯ: Скасовано ---
        save_history(app_obj, g.user, "status_change")

        db.session.commit()
        flash("Заявку було скасовано.", "success")
        return redirect(url_for("view_application", application_id=application_id))

    @app.route("/applications/file/<int:file_id>/delete", methods=["POST"])
    @login_required
    def delete_file_route(file_id):
        # ВИПРАВЛЕНО: db.get_or_404
        file_record = db.get_or_404(ApplicationFile, file_id)

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

    @app.route("/uploads/<filename>")
    def download_file(filename):
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            return abort(404)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)