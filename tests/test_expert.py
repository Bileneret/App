from extensions import db
from models import Application


def test_expert_dashboard_access(client, expert):
    client.post("/login", data={"email": expert.email, "password": "expert123"})
    response = client.get("/expert/applications")
    assert response.status_code == 200
    assert "Заявки на розгляді" in response.get_data(as_text=True)


def test_applicant_cannot_access_expert_dashboard(client, user):
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})
    response = client.get("/expert/applications", follow_redirects=True)
    assert "У вас немає прав" in response.get_data(as_text=True) or "немає прав" in response.get_data(as_text=True)


def test_expert_review_workflow(client, expert, user):
    with client.application.app_context():
        app_obj = Application(title="For Review", short_description="Desc", owner_id=user.id, status="submitted")
        db.session.add(app_obj)
        db.session.commit()
        app_id = app_obj.id

    client.post("/login", data={"email": expert.email, "password": "expert123"})

    # 1. Тест на відхилення БЕЗ коментаря
    response = client.post(f"/expert/applications/{app_id}", data={
        "decision": "rejected",
        "comment": ""
    }, follow_redirects=True)
    # Перевіряємо клас повідомлення або частину тексту, щоб уникнути проблем з кодуванням
    html = response.get_data(as_text=True)
    assert "danger" in html and ("коментар" in html)

    # 2. Успішне схвалення
    response = client.post(f"/expert/applications/{app_id}", data={
        "decision": "approved",
        "comment": "Good job"
    }, follow_redirects=True)

    assert "Заявку переведено у статус: approved" in response.get_data(as_text=True)

    with client.application.app_context():
        assert db.session.get(Application, app_id).status == "approved"