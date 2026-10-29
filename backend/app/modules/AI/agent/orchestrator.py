"""Chọn và gọi tool phù hợp với yêu cầu của người dùng.

Đây là bộ điều phối theo luật từ khóa (đơn giản, miễn phí, dễ giải thích khi bảo vệ).
Muốn nâng cấp thì thay hàm choose_tool bằng một LLM có hỗ trợ gọi tool.
"""
from sqlalchemy.orm import Session

from app.modules.ai.agent.tools import TOOLS
from app.modules.ai.matching.embeddings import strip_accents
from app.modules.auth.models import User

_RECOMMEND_KEYWORDS = (
    "goi y", "phu hop voi toi", "nen ung tuyen", "tim viec cho toi", "recommend", "suggest", "vi tri nao hop",
)


def choose_tool(user: User, message: str) -> str:
    text = strip_accents(message.lower())
    if user.role == "student" and any(k in text for k in _RECOMMEND_KEYWORDS):
        return "recommend_internships"
    return "ask_knowledge"


def run(db: Session, user: User, message: str) -> dict:
    name = choose_tool(user, message)
    result = TOOLS[name].run(db, user, message)
    return {"tool": name, "answer": result["answer"], "data": result["data"]}
