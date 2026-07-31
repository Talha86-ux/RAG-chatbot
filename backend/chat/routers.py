import logging
from fastapi import HTTPException, APIRouter
from rag_chain import answer_question
from .schema import ChatRequest, ChatResponse

logger = logging.getLogger("uvicorn.error")
chat_router = APIRouter()


@chat_router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer, sources = answer_question(req.question, k=req.k)
    except Exception as e:
        logger.exception("Error in /chat endpoint")  # prints full traceback to terminal
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(answer=answer, sources=sources)