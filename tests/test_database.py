import pytest
from sqlalchemy.exc import IntegrityError
from extensions import db
# ВИПРАВЛЕНО: Прибрали Author, додали ApplicationFile
from models import User, Application, ApplicationFile


def test_database_relationship_chain(app):
    """
    Тестування ланцюжка: User -> Application -> ApplicationFile.
    Перевіряємо, що дані коректно зберігаються на всіх 3 рівнях.
    """
    with app.app_context():
        # 1. Створюємо Користувача
        u = User(email="chain_owner@test.com")
        u.set_password("123")
        db.session.add(u)
        db.session.commit()

        # 2. Створюємо Заявку для цього користувача
        app_obj = Application(title="Chain App", short_description="Desc", owner=u)
        db.session.add(app_obj)
        db.session.commit()

        # 3. Створюємо Файли для цієї заявки (замість неіснуючих Авторів)
        file1 = ApplicationFile(filename="doc1.txt", application=app_obj)
        file2 = ApplicationFile(filename="doc2.pdf", application=app_obj)
        db.session.add_all([file1, file2])
        db.session.commit()

        # --- ПЕРЕВІРКА (Retrieval) ---
        # Витягуємо юзера і перевіряємо, чи бачить він файли через заявку
        user_from_db = db.session.get(User, u.id)

        # Перевірка зв'язку User -> Application
        assert len(user_from_db.applications) == 1
        my_app = user_from_db.applications[0]
        assert my_app.title == "Chain App"

        # Перевірка зв'язку Application -> ApplicationFile
        assert len(my_app.files) == 2
        # Перевіряємо наявність імен файлів
        filenames = {f.filename for f in my_app.files}
        assert "doc1.txt" in filenames
        assert "doc2.pdf" in filenames


def test_database_constraints_unique_email(app):
    """
    Тестування обмеження UNIQUE на полі User.email.
    База даних не повинна дозволити створити дублікат.
    """
    with app.app_context():
        u1 = User(email="unique@test.com")
        u1.set_password("123")
        db.session.add(u1)
        db.session.commit()

        u2 = User(email="unique@test.com")  # Той самий email
        u2.set_password("456")
        db.session.add(u2)

        # Очікуємо помилку IntegrityError від БД
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_database_constraints_not_null(app):
    """
    Тестування обмеження NOT NULL (наприклад, Application.title).
    """
    with app.app_context():
        u = User(email="null_test@test.com")
        u.set_password("123")
        db.session.add(u)
        db.session.commit()

        # Спробуємо створити заявку без заголовка (title=None)
        app_bad = Application(title=None, short_description="Desc", owner=u)
        db.session.add(app_bad)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_database_function_password_hashing(app):
    """
    Тестування функції/методу БД (бізнес-логіка на рівні моделі).
    Перевіряємо, що set_password та check_password працюють коректно.
    """
    u = User(email="func@test.com")
    u.set_password("secret123")

    # Перевіряємо, що в базі лежить хеш, а не чистий пароль
    assert u.password_hash != "secret123"
    assert u.check_password("secret123") is True
    assert u.check_password("wrong") is False