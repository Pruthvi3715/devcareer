"""
/chat endpoints — RAG-powered profile chatbot.
Requires authentication (JWT). Rate-limited.
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from models.user import User
from models.chat_schema import ChatRequest, ChatResponse, SourceRef, ConversationSummary
from models.db import get_db
from services.auth import SECRET_KEY, ALGORITHM
from services import chat_engine, rate_limiter, vector_store

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Reusable auth dependency — validates JWT and returns User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/message", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a chat message. Returns AI response with source citations.
    Rate-limited: 20/min per user, 60/min global.
    """
    user_id = current_user.email

    # --- Rate limit check ---
    allowed, retry_after, reason = rate_limiter.check_rate_limit(user_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {reason}. Try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    # --- Check if user has any vectorized data ---
    doc_count = vector_store.get_document_count(user_id)
    if doc_count == 0:
        # Try to check by email without the domain for flexibility
        pass  # Will still work — chat engine handles empty context gracefully

    # --- Chat ---
    result = chat_engine.chat(
        user_id=user_id,
        message=body.message,
        conversation_id=body.conversation_id,
    )

    # Build response
    sources = [
        SourceRef(
            type=s["type"],
            repo_name=s.get("repo_name"),
            detail=s["detail"],
            relevance=s.get("relevance", 0),
        )
        for s in result.get("sources", [])
    ]

    remaining = rate_limiter.get_remaining(user_id)

    return ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
        sources=sources,
        rate_limit=remaining,
    )


@router.get("/history/{conversation_id}")
async def get_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get conversation history."""
    messages = chat_engine.get_conversation_history(conversation_id, current_user.email)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": messages}


@router.delete("/history/{conversation_id}")
async def delete_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation."""
    success = chat_engine.delete_conversation(conversation_id, current_user.email)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_user),
):
    """List all conversations for the current user."""
    return chat_engine.list_conversations(current_user.email)


@router.get("/status")
async def chat_status(
    current_user: User = Depends(get_current_user),
):
    """Check chat readiness: whether the user has vectorized data."""
    user_id = current_user.email
    doc_count = vector_store.get_document_count(user_id)
    remaining = rate_limiter.get_remaining(user_id)
    return {
        "ready": doc_count > 0,
        "document_count": doc_count,
        "rate_limit": remaining,
    }
