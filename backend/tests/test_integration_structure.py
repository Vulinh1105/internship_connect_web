from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.auth.models import User


def staff_headers(client):
    with SessionLocal() as db:
        db.add(User(email="staff@test.local", password_hash=hash_password("Test@1234"), role="staff"))
        db.commit()
    response = client.post("/api/auth/login", json={"email": "staff@test.local", "password": "Test@1234"})
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_managed_document_upload_list_and_index(client, monkeypatch):
    from app.modules.ai.rag.ingestion import pipeline
    headers = staff_headers(client)
    response = client.post("/api/documents", headers=headers,
                           files={"file": ("guide.txt", b"Knowledge for students", "text/plain")})
    assert response.status_code == 201, response.text
    document_id = response.json()["id"]
    assert response.json()["access_level"] == "public"
    assert client.get("/api/documents", headers=headers).json()[0]["id"] == document_id
    from app.modules.ai.rag.ingestion.validation import ingest_document
    with SessionLocal() as db:
        document, blocks = ingest_document(document_id, db)
        assert document.original_filename == "guide.txt"
        assert any("Knowledge" in b["text"] for b in blocks)
    def run(document_id, db):
        return pipeline.PipelineResult(document_id, pipeline.IndexingStatus.INDEXED, chunk_count=1)
    monkeypatch.setattr(pipeline, "run_pipeline_for_document", run)
    response = client.post(f"/api/documents/{document_id}/index", headers=headers)
    assert response.status_code == 200, response.text
    assert client.get(f"/api/documents/{document_id}", headers=headers).json()["status"] == "indexed"


def test_students_cannot_manage_knowledge(client, student):
    assert client.get("/api/documents", headers=student).status_code == 403
    assert client.post("/api/documents", headers=student,
                       files={"file": ("secret.txt", b"private", "text/plain")}).status_code == 403


def test_provider_failure_is_explicit(client, student, monkeypatch):
    from app.modules.ai.rag import rag_pipeline
    def fail(*args, **kwargs):
        raise RuntimeError("provider unavailable")
    monkeypatch.setattr(rag_pipeline, "run_rag", fail)
    assert client.post("/api/ai/chat", headers=student, json={"question": "test question"}).status_code == 503


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        self.refs.extend(v for k, v in attrs if k in {"href", "src"} and v)


def test_frontend_all_static_references_resolve(client):
    frontend = Path(__file__).resolve().parents[2] / "frontend"
    assert client.get("/app/").status_code == 200
    for page in frontend.rglob("*.html"):
        parser = References()
        parser.feed(page.read_text(encoding="utf-8"))
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or not url.path or url.path.startswith("/"):
                continue
            target = (page.parent / url.path).resolve()
            assert target.is_file(), (page, ref)
            path = target.relative_to(frontend).as_posix()
            assert client.get("/app/" + path).status_code == 200
