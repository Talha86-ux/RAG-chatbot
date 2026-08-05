import logging
from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from database import get_db
from rag_chain import answer_question
from .models import ChatSession, ChatMessage
from .schema import ChatRequest, ChatResponse, SessionOut, SessionCreate, MessageOut

logger = logging.getLogger("uvicorn.error")
chat_router = APIRouter()

HISTORY_LIMIT = 6  # last N messages used as conversational context


# ---------- Session management ----------

@chat_router.post("/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)):
    session = ChatSession(title=payload.title or "New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@chat_router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()


@chat_router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session.messages


@chat_router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    db.delete(session)
    db.commit()
    return {"status": "deleted"}


# ---------- Chat ----------

@chat_router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: DBSession = Depends(get_db)):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    recent = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(recent)]

    try:
        answer, sources = answer_question(req.question, k=req.k, history=history)
    except Exception as e:
        logger.exception("Error in /chat endpoint")
        raise HTTPException(status_code=500, detail=str(e))

    db.add_all([
        ChatMessage(session_id=session.id, role="user", content=req.question, sources=[]),
        ChatMessage(session_id=session.id, role="bot", content=answer, sources=sources),
    ])

    if session.title == "New Chat":
        session.title = req.question[:50]

    db.commit()

    return ChatResponse(answer=answer, sources=sources, session_id=session.id)