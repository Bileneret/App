import random
from app import app
from extensions import db
from models import User, Application

# --- КОНФІГУРАЦІЯ ---
PASSWORD = "Pass1234"  # Єдиний пароль для всіх тестових юзерів

# Список усіх можливих статусів
STATUSES = [
    "draft",
    "submitted",
    "needs_changes",
    "approved",
    "rejected",
    "cancelled"
]

# Набір слів для генерації назв
ADJECTIVES = ["Інноваційний", "Розумний", "Швидкий", "Автоматизований", "Цифровий", "Квантовий", "Екологічний"]
NOUNS = ["Алгоритм", "Метод", "Двигун", "Процесор", "Інтерфейс", "Аналізатор", "Синтезатор", "Модуль"]
DOMAINS = ["для навчання", "в медицині", "для фінансів", "у будівництві", "для космосу", "в агросекторі"]


def generate_title():
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)} {random.choice(DOMAINS)}"


def seed_data():
    with app.app_context():
        print(">>> Починаємо наповнення бази даних...")

        # 1. Створення користувачів
        print("--- Створення користувачів ---")

        users_to_create = [
            ("super_admin", 1, "super@test.com"),
            ("admin", 2, "admin{}@test.com"),
            ("expert", 3, "expert{}@test.com"),
            ("applicant", 10, "user{}@test.com")
        ]

        applicants = []  # Зберігаємо заявників, щоб прив'язати до них заявки

        for role, count, email_template in users_to_create:
            for i in range(1, count + 1):
                # Формуємо email (якщо один користувач - без цифри)
                email = email_template.format(i) if "{}" in email_template else email_template

                # Перевірка, чи існує
                user = User.query.filter_by(email=email).first()
                if not user:
                    user = User(email=email, role=role)
                    user.set_password(PASSWORD)
                    db.session.add(user)
                    print(f"[+] Створено {role}: {email}")
                else:
                    print(f"[!] Вже існує {role}: {email}")

                if role == "applicant":
                    applicants.append(user)

        # Зберігаємо користувачів, щоб отримати їх ID
        db.session.commit()

        # Отримуємо об'єкти заявників з бази (щоб мати ID)
        applicants = User.query.filter_by(role="applicant").all()

        if not applicants:
            print("Помилка: Немає заявників для створення заявок.")
            return

        # 2. Створення 50 заявок
        print("\n--- Створення 50 випадкових заявок ---")

        for i in range(50):
            owner = random.choice(applicants)
            status = random.choice(STATUSES)
            title = generate_title()
            description = (
                f"Це автоматично згенерована заявка №{i + 1}.\n"
                f"Вона має статус: {status}.\n"
                f"Автор заявки: {owner.email}.\n"
                "Тут міститься детальний опис винаходу або кориснї моделі..."
            )

            # Додаємо коментар, якщо статус відповідний
            comment = None
            if status in ["rejected", "needs_changes"]:
                comment = "Автоматичний коментар експерта: Будь ласка, уточніть деталі реалізації."

            app_obj = Application(
                title=title,
                short_description=description,
                status=status,
                owner_id=owner.id,
                expert_comment=comment
            )
            db.session.add(app_obj)

        db.session.commit()
        print(f"[+] Успішно створено 50 заявок.")
        print("\n>>> Наповнення завершено!")
        print(f">>> Пароль для всіх акаунтів: {PASSWORD}")


if __name__ == "__main__":
    seed_data()