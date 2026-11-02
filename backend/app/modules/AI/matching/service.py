"""AI1 - Gß╗úi ├╜ vß╗ï tr├¡ thß╗▒c tß║¡p ph├╣ hß╗úp vß╗¢i hß╗ô s╞í sinh vi├¬n."""
import hashlib
from datetime import date

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.ai.matching.embeddings import get_embedder
from app.modules.ai.matching.ranking import rank_candidates
from app.modules.ai.matching.vector_store import get_store
from app.modules.auth.models import User
from app.modules.internships.models import Internship
from app.modules.students import service as students_service

COLLECTION = "internships"
_state = {"fingerprint": None}


def internship_text(i: Internship) -> str:
    # Lß║╖p ti├¬u ─æß╗ü ─æß╗â t─âng trß╗ìng sß╗æ
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
    """Buß╗Öc lß║ºn gß╗úi ├╜ tiß║┐p theo dß╗▒ng lß║íi chß╗ë mß╗Ñc vector."""
    _state["fingerprint"] = None


def sync_index(internships: list[Internship]) -> int:
    """Chß╗ë dß╗▒ng lß║íi chß╗ë mß╗Ñc khi dß╗» liß╗çu tin thß╗▒c tß║¡p thay ─æß╗òi. Trß║ú vß╗ü sß╗æ tin ─æ├ú lß║¡p chß╗ë mß╗Ñc."""
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
        raise HTTPException(400, "Hß╗ô s╞í c├▓n trß╗æng. H├úy bß╗ò sung ng├ánh hß╗ìc hoß║╖c kß╗╣ n─âng ─æß╗â nhß║¡n gß╗úi ├╜")

    internships = _open_internships(db)
    if not internships:
        return []
    sync_index(internships)

    embedder = get_embedder()
    hits = get_store().search(COLLECTION, embedder.embed(query_text), max(top_k * 3, top_k))
    by_id = {i.id: i for i in internships}
    hits = [h for h in hits if h[0] in by_id]  # bß╗Å tin ─æ├ú ─æ├│ng nh╞░ng c├▓n s├│t trong chß╗ë mß╗Ñc

    ranked = rank_candidates(hits, skills, top_k)
    for r in ranked:
        r["internship"] = by_id[r["internship_id"]]
    return ranked
