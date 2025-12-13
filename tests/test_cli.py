from models import User


def test_init_db_command(runner):
    """Тест команди init-db."""
    result = runner.invoke(args=["init-db"])
    assert "Базу даних ініціалізовано." in result.output


def test_create_expert_command(runner, app):
    """Тест команди create-expert."""
    # 1. Успішне створення
    result = runner.invoke(args=["create-expert"])
    assert "Створено експерта" in result.output

    # 2. Вже існує
    result = runner.invoke(args=["create-expert"])
    assert "Експерт вже існує" in result.output


def test_create_admin_command(runner, app):
    """Тест команди create-admin."""
    result = runner.invoke(args=["create-admin"])
    assert "Створено звичайного адміна" in result.output

    result = runner.invoke(args=["create-admin"])
    assert "Адмін вже існує" in result.output


def test_create_super_admin_command(runner, app):
    """Тест команди create-super-admin."""
    result = runner.invoke(args=["create-super-admin"])
    assert "Створено ГОЛОВНОГО адміна" in result.output

    result = runner.invoke(args=["create-super-admin"])
    assert "Головний адмін вже існує" in result.output