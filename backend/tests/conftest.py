"""Cấu hình chung cho kiểm thử: dùng SQLite trong bộ nhớ, không đụng tới MySQL thật."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Phải đặt TRƯỚC khi import app
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["VECTOR_BACKEND"] = "memory"
os.environ["LLM_API_KEY"] = ""
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="ic_uploads_")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.modules.ai.matching import service as matching_service
from app.modules.ai.rag import retriever

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
