from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.modules.ai.agents import orchestrator
from app.modules.ai.matching import service as matching_service
from app.modules.ai.rag import service as rag_service
from app.modules.ai.matching.vector_store import get_store
from app.modules.ai.schemas import RecommendationOut, ChatRequest, ChatResponse, AgentRequest, AgentResponse
from app.modules.auth.models import User
from app.modules.internships.schemas import InternshipOut

router = APIRouter(prefix="/api/ai", tags=["AI - Gợi ý & Chatbot"])


@router.get("/status")
def ai_status(user: User = Depends(get_current_user)):
    from app.core.config import settings
    return {
        "provider": "openai",
        "chat_model": settings.OPENAI_CHAT_MODEL,
        "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
        "configured": bool(settings.OPENAI_API_KEY),
        "matching_backend": settings.EMBEDDING_BACKEND,
    }


@router.get("/recommendations", response_model=list[RecommendationOut])
def recommendations(
    top_k: int = Query(5, ge=1, le=20),
    user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    items = matching_service.recommend(db, user, top_k)
    return [
        RecommendationOut(
            internship=InternshipOut.model_validate(r["internship"]),
            score=r["score"],
            matched_skills=r["matched_skills"],
        )
        for r in items
    ]


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return rag_service.ask(db, data.question.strip(), session_id=f"user:{user.id}")


@router.post("/agent", response_model=AgentResponse)
def agent(data: AgentRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return orchestrator.run(db, user, data.message.strip(), data.tool)


@router.post("/reindex")
def reindex(_user: User = Depends(require_role("staff", "admin")), db: Session = Depends(get_db)):
    """Dựng lại chỉ mục vector từ dữ liệu hiện tại."""
    matching_service.reset_index()
    from app.modules.documents.service import reindex_knowledge
    n_internships = matching_service.sync_index(matching_service._open_internships(db))
    documents = reindex_knowledge(db)
    rag_service.reset_index()
    return {"internships_indexed": n_internships, "documents": documents, "vector_backend": get_store().backend}
