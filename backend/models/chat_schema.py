"""
Pydantic schemas for the Chat feature.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class SourceRef(BaseModel):
    type: str  # finding, verdict, gap, roadmap, resume, etc.
    repo_name: Optional[str] = None
    detail: str  # Short description of what this source is
    relevance: float = 0.0


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    sources: Optional[List[SourceRef]] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: List[SourceRef] = []
    rate_limit: dict = {}  # remaining quota


class ConversationSummary(BaseModel):
    conversation_id: str
    created_at: str
    last_message_at: str
    message_count: int
    preview: str  # First user message truncated
