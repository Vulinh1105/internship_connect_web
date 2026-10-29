from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.modules.ai.agent import orchestrator
from app.modules.ai.matching import service as matching_service
from app.modules.ai.rag import retriever
from app.modules.ai.rag import service as rag_service
from app.modules.ai.vector_store import get_store
from app.modules.auth.models import User
from app.modules.internships.schemas import InternshipOut

router = APIRouter(prefix="/api/ai", tags=["AI - Gợi ý & Chatbot"])


class RecommendationOut(BaseModel):
    internship: InternshipOut
    score: float
    matched_skills: list[str]


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class SourceOut(BaseModel):
    title: str
    source: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    mode: str  # llm | extractive | no_context
    sources: list[SourceOut]


class AgentRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


class AgentResponse(BaseModel):
    tool: str
    answer: str
    data: list | dict | None = None


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
def chat(data: ChatRequest, _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return rag_service.ask(db, data.question.strip())


@router.post("/agent", response_model=AgentResponse)
def agent(data: AgentRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return orchestrator.run(db, user, data.message.strip())


@router.post("/reindex")
def reindex(_user: User = Depends(require_role("staff", "admin")), db: Session = Depends(get_db)):
    """Dựng lại chỉ mục vector từ dữ liệu hiện tại."""
    matching_service.reset_index()
    retriever.reset_index()
    n_internships = matching_service.sync_index(matching_service._open_internships(db))
    n_chunks = retriever.sync_index(db)
    return {"internships_indexed": n_internships, "knowledge_chunks": n_chunks, "vector_backend": get_store().backend}
