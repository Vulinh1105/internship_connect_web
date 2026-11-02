"""Cấu hình chung cho kiểm thử: dùng SQLite trong bộ nhớ, không đụng tới MySQL thật."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Phải đặt TRƯỚC khi import app
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["KNOWLEDGE_AUTO_INDEX"] = "false"
os.environ["VECTOR_BACKEND"] = "memory"
os.environ["EMBEDDING_BACKEND"] = "hashing"
os.environ["LLM_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = "test-key-not-used-for-network"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="ic_uploads_")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.modules.ai.matching import service as matching_service
from app.modules.ai.rag import service as retriever

PASSWORD = "Test@1234"


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    matching_service.reset_index()
    retriever.reset_index()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_user(client):
    """make_user("a@x.com", "student") -> header Authorization dùng cho request."""

    def _make(email: str, role: str):
        r = client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "role": role})
        assert r.status_code == 201, r.text
        r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return {"Authorization": "Bearer " + r.json()["access_token"]}

    return _make


@pytest.fixture
def student(client, make_user):
    headers = make_user("sv@example.com", "student")
    r = client.put(
        "/api/students/me",
        headers=headers,
        json={"full_name": "Nguyen Van A", "student_code": "SV001", "major": "Công nghệ thông tin"},
    )
    assert r.status_code == 200, r.text
    return headers


@pytest.fixture
def company(client, make_user):
    headers = make_user("dn@example.com", "company")
    r = client.post("/api/companies", headers=headers, json={"company_name": "Cong ty Test"})
    assert r.status_code == 201, r.text
    return headers


def approve_post(client, internship_id):
    """Explicit human-review step for legacy published-post test fixtures."""
    from app.core.database import SessionLocal
    from app.modules.auth.models import User
    from app.core.security import hash_password, create_access_token
    from sqlalchemy import select
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == "reviewer@tests.local"))
        if admin is None:
            admin = User(email="reviewer@tests.local", role="admin", password_hash=hash_password("Review@123"))
            db.add(admin); db.commit()
        token = create_access_token(admin.id, admin.role)
    response = client.post(f"/api/internships/{internship_id}/review", headers={"Authorization": "Bearer " + token}, json={"decision": "approved"})
    assert response.status_code == 200, response.text
    return response.json()
