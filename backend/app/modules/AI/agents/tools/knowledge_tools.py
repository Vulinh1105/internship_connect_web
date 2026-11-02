from app.modules.ai.rag.service import ask
def ask_knowledge(db, user, message):
    return ask(db, message, session_id=f"user:{user.id}")
