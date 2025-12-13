from extensions import db
from models import Application


def test_expert_dashboard_access(client, expert, user):
    # Звичайний юзер
    client.post("/login", data={"email": user.email, "password": "StrongPass1"})
    resp = client.get("/expert/applications", follow_redirects=True)
    assert "У вас немає прав доступу" in resp.get_data(as_text=True)
    client.get("/logout")

    # Експерт
    client.post("/login", data={"email": expert.email, "password": "ExpertPass1"})
    resp = client.get("/expert/applications")
    assert resp.status_code == 200


def test_expert_reject_requires_comment(client, app, expert, user):
    """Відхилення заявки вимагає коментаря."""
    with app.app_context():
        u = db.session.merge(user)
        app_obj = Application(title="To Reject", short_description="Desc", owner=u, status="submitted")
        db.session.add(app_obj)
        db.session.commit()
        app_id = app_obj.id

    client.post("/login", data={"email": expert.email, "password": "ExpertPass1"})

    # Спроба відхилити без коментаря
    response = client.post(f"/expert/applications/{app_id}", data={
        "decision": "rejected",
        "comment": ""
    }, follow_redirects=True)

    text = response.get_data(as_text=True)
    # ВИПРАВЛЕНО: Спрощена перевірка тексту (без апострофа)
    assert "коментар" in text
    assert "обов'язковим" in text or "обов" in text

    # Відхилення з коментарем
    response = client.post(f"/expert/applications/{app_id}", data={
        "decision": "rejected",
        "comment": "Bad quality"
    }, follow_redirects=True)

    assert "Заявку переведено у статус: rejected" in response.get_data(as_text=True)


def test_expert_cannot_review_own_application(client, app, expert):
    """Експерт не може оцінювати власну заявку."""
    with app.app_context():
        e = db.session.merge(expert)
        app_obj = Application(title="My App", short_description="Desc", owner=e, status="submitted")
        db.session.add(app_obj)
        db.session.commit()
        app_id = app_obj.id

    client.post("/login", data={"email": expert.email, "password": "ExpertPass1"})
    response = client.get(f"/expert/applications/{app_id}", follow_redirects=True)

    assert "Ви не можете оцінювати власні заявки" in response.get_data(as_text=True)