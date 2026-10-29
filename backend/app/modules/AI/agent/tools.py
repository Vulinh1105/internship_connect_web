"""Khai báo các tool mà agent có thể gọi: gợi ý việc làm (matching) và hỏi đáp (RAG)."""
from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session

from app.modules.ai.matching import service as matching_service
from app.modules.ai.rag import service as rag_service
from app.modules.auth.models import User


@dataclass
class Tool:
    name: str
    description: str
    run: Callable[[Session, User, str], dict]


def _recommend(db: Session, user: User, message: str) -> dict:
    items = matching_service.recommend(db, user, top_k=5)
    if not items:
        return {"answer": "Hiện chưa có vị trí thực tập nào đang mở để gợi ý.", "data": []}
    lines = [
        f"{n}. {r['internship'].title} - {r['internship'].company_name} (độ phù hợp {r['score']:.0%})"
        for n, r in enumerate(items, start=1)
    ]
    data = [
        {
            "internship_id": r["internship_id"],
            "title": r["internship"].title,
            "company"
            "_name": r["internship"].company_name,
            "score": r["score"],
            "matched_skills": r["matched_skills"],
        }
        for r in items
    ]
    return {"answer": "Các vị trí phù hợp nhất với hồ sơ của bạn:\n" + "\n".join(lines), "data": data}


def _ask(db: Session, user: User, message: str) -> dict:
    result = rag_service.ask(db, message)
    return {"answer": result["answer"], "data": result["sources"]}


TOOLS = {
    "recommend_internships": Tool(
        "recommend_internships", "Gợi ý vị trí thực tập phù hợp với hồ sơ sinh viên", _recommend
    ),
    "ask_knowledge": Tool("ask_knowledge", "Trả lời câu hỏi về quy trình và các tin thực tập", _ask),
}
