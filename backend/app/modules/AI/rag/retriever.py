"""Tìm các đoạn tài liệu liên quan đến câu hỏi: FAQ + các tin thực tập đang mở."""
import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.modules.ai.matching.service import _open_internships, internship_text
from app.modules.ai.rag.embeddings import get_embedder
from app.modules.ai.vector_store import get_store

COLLECTION = "knowledge"
FAQ_PATH = Path(__file__).parent / "knowledge" / "faq.md"
MIN_SCORE = 0.08  # dưới ngưỡng này coi như không liên quan
_state = {"fingerprint": None}


def load_faq_chunks() -> list[dict]:
    """Tách faq.md thành từng mục theo tiêu đề '## '."""
    text = FAQ_PATH.read_text(encoding="utf-8")
    chunks = []
    for block in text.split("## ")[1:]:
        title, _, body = block.partition("\n")
        chunks.append({"title": title.strip(), "text": f"{title.strip()}. {body.strip()}", "source": "faq"})
    return chunks


def build_chunks(db: Session) -> list[dict]:
    chunks = load_faq_chunks()
    for i in _open_internships(db):
        chunks.append(
            {
                "title": f"{i.title} - {i.company_name}",
                "text": internship_text(i),
                "source": f"internship:{i.id}",
            }
        )
    return chunks


def reset_index() -> None:
    _state["fingerprint"] = None


def sync_index(db: Session) -> int:
    chunks = build_chunks(db)
    fingerprint = hashlib.sha1(repr([(c["source"], c["text"]) for c in chunks]).encode()).hexdigest()
    if fingerprint != _state["fingerprint"]:
        embedder = get_embedder()
        items = [(n, embedder.embed(c["text"]), c) for n, c in enumerate(chunks, start=1)]
        get_store().replace(COLLECTION, items, embedder.dim)
        _state["fingerprint"] = fingerprint
    return len(chunks)


def retrieve(db: Session, question: str, top_k: int = 4) -> list[dict]:
    sync_index(db)
    hits = get_store().search(COLLECTION, get_embedder().embed(question), top_k)
    results = []
    for _id, score, payload in hits:
        if score >= MIN_SCORE:
            results.append({**payload, "score": round(float(score), 4)})
    return results
