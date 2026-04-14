from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationRead(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[int] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    message_id: int
