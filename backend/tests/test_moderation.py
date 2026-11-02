from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.modules.auth.models import User
from app.modules.internships.models import Internship, Application
from app.modules.ai.matching.service import _open_internships


def reviewer(role="staff"):
    with SessionLocal() as db:
        user = User(email=f"{role}@review.test", role=role, password_hash="unused")
        db.add(user); db.commit()
        return {"Authorization": "Bearer " + create_access_token(user.id, role)}


def post(client, company, **extra):
    response = client.post("/api/internships", headers=company, json={"title": "Python Intern", "description": "Build APIs", "requirements": "Python", **extra})
    assert response.status_code == 201, response.text
    return response.json()


def test_pending_hidden_until_human_review(client, company, student):
    item = post(client, company)
    id = item["id"]
    assert item["moderation_status"] == "pending"
    assert client.get("/api/internships").json()["total"] == 0
    assert client.get(f"/api/internships/{id}").status_code == 404
    assert client.post(f"/api/internships/{id}/applications", headers=student, json={}).status_code == 400
    with SessionLocal() as db: assert not _open_internships(db)
    assert client.post(f"/api/internships/{id}/review", headers=company, json={"decision": "approved"}).status_code == 403
    staff = reviewer()
    assert client.get("/api/internships/moderation", headers=student).status_code == 403
    assert client.get("/api/internships/moderation", headers=staff).json()["total"] == 1
    assert client.post(f"/api/internships/{id}/review", headers=staff, json={"decision": "approved"}).status_code == 200
    assert client.get(f"/api/internships/{id}").status_code == 200
    with SessionLocal() as db: assert len(_open_internships(db)) == 1
    assert client.put(f"/api/internships/{id}", headers=company, json={"description": "Changed"}).json()["moderation_status"] == "pending"
    assert client.get(f"/api/internships/{id}").status_code == 404


def test_flags_rejection_and_no_self_approval(client, company):
    item = post(client, company, description="Yêu cầu đóng phí tuyển dụng và đặt cọc")
    assert "đóng phí" in item["auto_flags"]
    staff = reviewer("admin")
    url = f"/api/internships/{item['id']}/review"
    assert client.post(url, headers=staff, json={"decision": "rejected", "reason": " "}).status_code == 400
    response = client.post(url, headers=staff, json={"decision": "rejected", "reason": "Không thu phí ứng viên"})
    assert response.json()["rejection_reason"] == "Không thu phí ứng viên"
    assert response.json()["reviewed_by"] is not None
    assert client.put(f"/api/internships/{item['id']}", headers=company, json={"status": "open", "moderation_status": "approved"}).json()["moderation_status"] == "rejected"


def test_soft_delete_permissions_and_history(client, company, student, make_user):
    item = post(client, company)
    staff = reviewer()
    id = item["id"]
    client.post(f"/api/internships/{id}/review", headers=staff, json={"decision": "approved"})
    application = client.post(f"/api/internships/{id}/applications", headers=student, json={})
    assert application.status_code == 201
    other = make_user("other@company.test", "company")
    client.post("/api/companies", headers=other, json={"company_name": "Other"})
    assert client.delete(f"/api/internships/{id}", headers=other).status_code == 403
    assert client.delete(f"/api/internships/{id}", headers=student).status_code == 403
    assert client.delete(f"/api/internships/{id}", headers=company).status_code == 204
    assert client.get(f"/api/internships/{id}").status_code == 404
    assert client.get("/api/internships/mine", headers=company).json()["total"] == 0
    with SessionLocal() as db:
        assert db.get(Internship, id).deleted_at is not None
        assert db.get(Application, application.json()["id"]) is not None
        assert not _open_internships(db)
    another = post(client, company)
    assert client.delete(f"/api/internships/{another['id']}", headers=staff).status_code == 204


def test_cannot_register_privileged_role(client):
    for role in ("staff", "admin"):
        assert client.post("/api/auth/register", json={"email": "attacker@test.local", "password": "Password@123", "role": role}).status_code == 422
