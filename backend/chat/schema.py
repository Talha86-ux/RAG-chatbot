from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    k: int = 4


class ChatResponse(BaseModel):
    answer: str
    sources: list
