"""AI2 - Chatbot hỏi đáp về thực tập (RAG: tìm tài liệu rồi sinh câu trả lời)."""
from sqlalchemy.orm import Session

from . import generator, retriever


def ask(db: Session, question: str, top_k: int = 4) -> dict:
    chunks = retriever.retrieve(db, question, top_k)
    result = generator.generate_answer(question, chunks)
    return {
        "answer": result["answer"],
        "mode": result["mode"],
        "sources": [{"title": c["title"], "source": c["source"], "score": c["score"]} for c in chunks],
    }
