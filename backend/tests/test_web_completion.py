from pathlib import Path
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.core.security import hash_password


def administrator(client):
    with SessionLocal() as db:
        db.add(User(email="admin@web.test", password_hash=hash_password("Test@1234"), role="admin"))
        db.commit()
    result = client.post("/api/auth/login", json={"email": "admin@web.test", "password": "Test@1234"})
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def test_admin_dashboard_endpoints(client, student, company):
    admin = administrator(client)
    students = client.get("/api/students?page=1&page_size=10", headers=admin)
    assert students.status_code == 200, students.text
    assert students.json()["items"][0]["full_name"] == "Nguyen Van A"
    assert client.get("/api/students", headers=student).status_code == 403
    assert client.get("/api/students?page_size=101", headers=admin).status_code == 422
    assert client.get("/api/companies?page_size=10", headers=admin).json()["total"] == 1
    assert client.get("/api/internships/stats", headers=admin).status_code == 200
    assert client.get("/api/auth/users", headers=admin).json()["total"] == 3


def test_openai_status_does_not_expose_secret(client, student):
    response = client.get("/api/ai/status", headers=student)
    assert response.status_code == 200
    assert response.json()["provider"] == "openai"
    assert response.json()["chat_model"] == "gpt-4o-mini"
    assert "test-key-not-used-for-network" not in response.text


def test_openai_clients_use_one_key_and_small_models():
    from app.modules.ai.providers.openai_client import create_chat_model, create_embeddings
    llm = create_chat_model(max_tokens=200)
    embedding = create_embeddings()
    assert llm.model_name == "gpt-4o-mini"
    assert llm.max_tokens == 200
    assert embedding.model == "text-embedding-3-small"
    assert llm.openai_api_key.get_secret_value() == embedding.openai_api_key.get_secret_value()


def test_cv_preview_checks_ownership(client, student, make_user):
    response = client.post("/api/students/me/cvs", headers=student,
                           files={"file": ("cv.pdf", b"%PDF-test", "application/pdf")})
    assert response.status_code == 201, response.text
    cv_id = response.json()["id"]
    assert client.get(f"/api/students/me/cvs/{cv_id}/download", headers=student).content == b"%PDF-test"
    other = make_user("other@web.test", "student")
    client.put("/api/students/me", headers=other, json={"full_name": "Other"})
    assert client.get(f"/api/students/me/cvs/{cv_id}/download", headers=other).status_code == 404


def test_pending_upload_can_be_deleted_without_qdrant(client):
    admin = administrator(client)
    response = client.post("/api/documents", headers=admin,
                           files={"file": ("guide.txt", b"Public guide", "text/plain")})
    assert response.status_code == 201
    document_id = response.json()["id"]
    assert client.delete(f"/api/documents/{document_id}", headers=admin).status_code == 204
    assert client.get(f"/api/documents/{document_id}", headers=admin).status_code == 404


def test_chat_missing_key_is_actionable(client, student, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    response = client.post("/api/ai/chat", headers=student, json={"question": "Quy trình thực tập?"})
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_root_opens_web(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/app/"
