from functools import wraps
from flask import session, g, flash, redirect, request, url_for
from flask_mail import Message
from models import User
from extensions import db, mail


def send_password_reset_email(to_email: str, reset_link: str):
    print("=== ЛИСТ ДЛЯ ВІДНОВЛЕННЯ ПАРОЛЯ ===")
    print(f"Кому: {to_email}")
    print(f"Посилання: {reset_link}")
    print("====================================")

    try:
        msg = Message("Відновлення пароля", recipients=[to_email])
        msg.body = f"Для відновлення пароля перейдіть за посиланням: {reset_link}"
        mail.send(msg)
    except Exception as e:
        print(f"Помилка відправки листа відновлення: {e}")

    return


def send_status_update_email(application):
    """Відправляє стилізований HTML-лист (банер)."""

    # Словник перекладу статусів
    STATUS_TRANSLATIONS = {
        "approved": "✅ Схвалено (Approved)",
        "rejected": "❌ Відхилено (Rejected)",
        "needs_changes": "⚠️ Потребує змін (Needs Changes)",
        "submitted": "На розгляді",
        "draft": "Чернетка",
        "cancelled": "Скасовано"
    }

    readable_status = STATUS_TRANSLATIONS.get(application.status, application.status)
    subject = f"Оновлення заявки №{application.id}"
    recipient = application.owner.email

    # Посилання на заявку (генеруємо повний URL)
    # _external=True створює посилання з http://...
    app_link = url_for('view_application', application_id=application.id, _external=True)

    # --- HTML ШАБЛОН ЛИСТА ---
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #121212; /* Темний фон всієї сторінки */
                color: #e0e0e0;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #1e1e1e; /* Фон картки */
                border: 1px solid #333;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
            .header {{
                background-color: #1e1e1e;
                padding: 30px;
                text-align: center;
                border-bottom: 1px solid #333;
            }}
            .header h1 {{
                margin: 0;
                color: #ffffff;
                font-size: 24px;
            }}
            .content {{
                padding: 30px;
                color: #cccccc;
                line-height: 1.6;
            }}
            .info-block {{
                background-color: #2d2d2d; /* Фон блоку з даними */
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #3b82f6; /* Синя лінія зліва */
            }}
            .info-item {{
                margin-bottom: 10px;
            }}
            .label {{
                font-weight: bold;
                color: #ffffff;
            }}
            .status-text {{
                color: #fcd34d; /* Жовтий для статусу */
                font-weight: bold;
                font-size: 1.1em;
            }}
            .comment-block {{
                margin-top: 20px;
                font-style: italic;
                color: #a0a0a0;
                border-left: 2px solid #555;
                padding-left: 10px;
            }}
            .btn-container {{
                text-align: center;
                margin-top: 30px;
                margin-bottom: 20px;
            }}
            .btn {{
                background-color: #065f46; /* Зелена кнопка */
                color: #ffffff !important;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                display: inline-block;
                transition: background 0.3s;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                font-size: 12px;
                color: #666;
                background-color: #181818;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Система керування заявками на авторські свідоцтва</h1>
            </div>

            <div class="content">
                <h2 style="color: white; margin-top: 0;">Вітаємо!</h2>
                <p>Ваша заявка <strong>№{application.id}</strong> отримала новий статус.</p>

                <div class="info-block">
                    <div class="info-item">
                        <span class="label">Назва Вашої заявки:</span><br>
                        {application.title}
                    </div>

                    <div class="info-item">
                        <span class="label">Опис вашої заявки:</span><br>
                        <span style="font-size: 0.9em;">{application.short_description[:200]}...</span>
                    </div>

                    <div class="info-item" style="margin-top: 15px;">
                        <span class="label">Отриманий статус:</span><br>
                        <span class="status-text">{readable_status}</span>
                    </div>

                    <div class="info-item">
                        <span class="label">Коментар від експерта:</span>
                        <div class="comment-block">
                            "{application.expert_comment or 'Без коментаря'}"
                        </div>
                    </div>
                </div>

                <div class="btn-container">
                    <a href="{app_link}" class="btn">Перейти до заявки</a>
                </div>
            </div>

            <div class="footer">
                &copy; 2025 Система керування заявками на авторські свідоцтва.<br>
                Це автоматичне повідомлення.
            </div>
        </div>
    </body>
    </html>
    """

    # Текстова версія
    text_body = f"""
    Вітаємо!
    Ваша заявка №{application.id} отримала новий статус!

    Назва: {application.title}
    Статус: {readable_status}
    Коментар: {application.expert_comment or 'Без коментаря'}

    Переглянути: {app_link}
    """

    print(f"\n[EMAIL DEBUG] Sending to: {recipient} | Subject: {subject}\n")

    try:
        msg = Message(subject, recipients=[recipient])
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        print("[EMAIL] Лист успішно відправлено.")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(**kwargs)

    return wrapped_view


def expert_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))
        if g.user.role not in ['expert', 'admin', 'super_admin']:
            flash("У вас немає прав доступу до цієї сторінки.", "danger")
            return redirect(url_for("index"))
        return view_func(**kwargs)

    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Будь ласка, увійдіть у систему.", "warning")
            return redirect(url_for("login", next=request.path))
        if g.user.role not in ['admin', 'super_admin']:
            flash("Доступ заборонено.", "danger")
            return redirect(url_for("index"))
        return view_func(**kwargs)

    return wrapped_view