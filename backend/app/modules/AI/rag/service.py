"""API adapter. The existing RAGPipeline owns all AI decisions."""
import logging
from fastapi import HTTPException
log = logging.getLogger(__name__)

def ask(db, question, session_id):
    from app.core.config import settings
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "Chưa cấu hình OPENAI_API_KEY trong file .env của backend. Liên hệ quản trị viên.")
    try:
        from .rag_pipeline import run_rag
        result = run_rag(question, session_id=session_id)
    except Exception as exc:
        log.exception("RAG dependency or provider unavailable")
        raise HTTPException(503, "Trợ lý AI tạm thời không thể xử lý câu hỏi. Vui lòng thử lại sau hoặc liên hệ quản trị viên.") from exc
    return {**result, "mode": "rag", "sources": [
        {"title": str(c.get("source", "")), "source": str(c.get("source", "")),
         "score": result.get("top_rerank_score") or 0.0}
        for c in result.get("citations", [])]}

def reset_index():
    from . import rag_pipeline
    rag_pipeline._pipeline = None
