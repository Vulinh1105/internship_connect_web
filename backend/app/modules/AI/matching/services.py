"""AI1 - Gợi ý vị trí thực tập phù hợp với hồ sơ sinh viên."""
import hashlib
from datetime import date

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.ai.matching.embeddings import get_embedder
from app.modules.ai.matching.ranking import rank_candidates
from app.modules.ai.vector_store import get_store
from app.modules.auth.models import User
from app.modules.internships.models import Internship
from app.modules.students import service as students_service

COLLECTION = "internships"
_state = {"fingerprint": None}


def internship_text(i: Internship) -> str:
    # Lặp tiêu đề để tăng trọng số
    parts = [i.title, i.title, i.requirements or "", i.description or "", i.location or "", i.company_name or ""]
    return ". ".join(p for p in parts if p)


def _open_internships(db: Session) -> list[Internship]:
    stmt = (
        select(Internship)
        .options(joinedload(Internship.company))
        .where(
            Internship.status == "open",
            or_(Internship.deadline.is_(None), Internship.deadline >= date.today()),
        )
        .order_by(Internship.id)
    )
    return list(db.scalars(stmt).unique())


def reset_index() -> None:
    """Buộc lần gợi ý tiếp theo dựng lại chỉ mục vector."""
    _state["fingerprint"] = None


def sync_index(internships: list[Internship]) -> int:
    """Chỉ dựng lại chỉ mục khi dữ liệu tin thực tập thay đổi. Trả về số tin đã lập chỉ mục."""
    texts = {i.id: internship_text(i) for i in internships}
    fingerprint = hashlib.sha1(repr(sorted(texts.items())).encode()).hexdigest()
    if fingerprint != _state["fingerprint"]:
        embedder = get_embedder()
        items = [(i.id, embedder.embed(texts[i.id]), {"text": texts[i.id]}) for i in internships]
        get_store().replace(COLLECTION, items, embedder.dim)
        _state["fingerprint"] = fingerprint
    return len(internships)


def recommend(db: Session, user: User, top_k: int = 5) -> list[dict]:
    student = students_service.require_student_profile(db, user)
    skills = [s.skill_name for s in student.skills]
    profile_parts = [student.major or "", " ".join(skills), " ".join(skills), student.profile_summary or ""]
    query_text = ". ".join(p for p in profile_parts if p.strip())
    if not query_text.strip():
        raise HTTPException(400, "Hồ sơ còn trống. Hãy bổ sung ngành học hoặc kỹ năng để nhận gợi ý")

    internships = _open_internships(db)
    if not internships:
        return []
    sync_index(internships)

    embedder = get_embedder()
    hits = get_store().search(COLLECTION, embedder.embed(query_text), max(top_k * 3, top_k))
    by_id = {i.id: i for i in internships}
    hits = [h for h in hits if h[0] in by_id]  # bỏ tin đã đóng nhưng còn sót trong chỉ mục

    ranked = rank_candidates(hits, skills, top_k)
    for r in ranked:
        r["internship"] = by_id[r["internship_id"]]
    return ranked
