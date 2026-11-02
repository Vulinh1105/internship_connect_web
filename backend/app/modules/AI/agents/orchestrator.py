"""Explicit tool dispatch: no invented keyword/LLM routing algorithm."""
from fastapi import HTTPException
from .registry import TOOLS
def run(db, user, message, tool="ask_knowledge"):
    if tool not in TOOLS:
        raise HTTPException(422, "Tool không được hỗ trợ")
    result = TOOLS[tool](db, user, message)
    return {"tool": tool, "answer": result.get("answer", ""), "data": result}
