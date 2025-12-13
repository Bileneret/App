import random
from app import app
from extensions import db
from models import User, Application, ApplicationFile

# --- КОНФІГУРАЦІЯ ---
PASSWORD = "Pass1234"

STATUSES = ["draft", "submitted", "needs_changes", "approved", "rejected", "cancelled"]
ADJECTIVES = ["Інноваційний", "Розумний", "Швидкий", "Автоматизований", "Цифровий", "Квантовий", "Екологічний"]
NOUNS = ["Алгоритм", "Метод", "Двигун", "Процесор", "Інтерфейс", "Аналізатор", "Синтезатор", "Модуль"]
DOMAINS = ["для навчання", "в медицині", "для фінансів", "у будівництві", "для космосу", "в агросекторі"]


def generate_title():
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)} {random.choice(DOMAINS)}"


def seed_data():
    with app.app_context():
        print(">>> Починаємо наповнення бази даних...")

        print("\n--- СТВОРЕННЯ КОРИСТУВАЧІВ ---")
        users_to_create = [
            ("super_admin", 1, "super@test.com"),
            ("admin", 2, "admin{}@test.com"),
            ("expert", 3, "expert{}@test.com"),
            ("applicant", 20, "user{}@test.com")
        ]

        applicants = []

        for role, count, email_template in users_to_create:
            for i in range(1, count + 1):
                email = email_template.format(i) if "{}" in email_template else email_template
                user = User.query.filter_by(email=email).first()
                if not user:
                    user = User(email=email, role=role)
                    user.set_password(PASSWORD)
                    db.session.add(user)
                    print(f"[+] Створено {role.upper()}:  Login: {email:<20} | Password: {PASSWORD}")
                else:
                    print(f"[!] Вже існує {role.upper()}:  Login: {email:<20} | Password: {PASSWORD}")

                if role == "applicant":
                    applicants.append(user)

        db.session.commit()
        applicants = User.query.filter_by(role="applicant").all()

        if not applicants:
            print("Помилка: Немає заявників.")
            return

        print("\n--- СТВОРЕННЯ ЗАЯВОК ---")
        for i in range(50):
            owner = random.choice(applicants)
            status = random.choice(STATUSES)

            comment = None
            if status in ["rejected", "needs_changes"]:
                comment = "Автоматичний коментар експерта."

            app_obj = Application(
                title=generate_title(),
                short_description=f"Автоматична заявка №{i + 1}...",
                status=status,
                owner_id=owner.id,
                expert_comment=comment
            )
            db.session.add(app_obj)
            db.session.flush()

            # Додаємо фейковий файл (запис у базу, без реального файлу)
            fake_file = ApplicationFile(filename=f"fake_doc_{i}.txt", application_id=app_obj.id)
            db.session.add(fake_file)

        db.session.commit()
        print("\n>>> ЗАВЕРШЕНО! База даних готова.")


if __name__ == "__main__":
    seed_data()