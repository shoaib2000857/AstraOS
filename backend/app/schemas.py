from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True

class ConversationCreate(BaseModel):
    title: Optional[str]

class ConversationRead(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = []

    class Config:
        orm_mode = True

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[int] = None
    model: Optional[str] = "local-instruct"

class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    message_id: int
