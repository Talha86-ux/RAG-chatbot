from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SourceItem(BaseModel):
    source: str
    snippet: str


class ChatRequest(BaseModel):
    question: str
    session_id: str
    k: int = 4


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    session_id: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: List[SourceItem] = []
    created_at: datetime

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"