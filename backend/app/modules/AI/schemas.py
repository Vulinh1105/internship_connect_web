from pydantic import BaseModel, Field
from app.modules.internships.schemas import InternshipOut


class RecommendationOut(BaseModel):
    internship: InternshipOut
    score: float
    matched_skills: list[str]


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class SourceOut(BaseModel):
    title: str
    source: str
    score: float = 0.0


class ChatResponse(BaseModel):
    answer: str
    mode: str = "rag"
    sources: list[SourceOut] = []


class AgentRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000)
    tool: str = "ask_knowledge"


class AgentResponse(BaseModel):
    tool: str
    answer: str
    data: list | dict | None = None
