"""
MindCare AI — Pydantic v2 Request/Response Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    is_crisis: bool
    crisis_message: Optional[str] = None
    hotline: Optional[str] = None


class MoodLogRequest(BaseModel):
    session_id: str
    mood_score: int = Field(..., ge=1, le=10)
    note: Optional[str] = None


class MoodLogResponse(BaseModel):
    success: bool
    message: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[Any]
