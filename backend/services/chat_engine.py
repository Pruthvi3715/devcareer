"""
Chat Engine — RAG-powered conversational AI for DevCareer profile chat.

Retrieves relevant context from the vector store, builds a system prompt
with the DevCareer Career Coach persona, and calls the existing LLM backend
for natural-language (non-JSON) responses.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from . import vector_store
from .claude_engine import (
    _get_client,
    _max_completion_tokens,
    _strip_model_wrappers,
    get_llm_model,
    llm_backend_label,
    get_llm_provider,
)

# In-memory conversation store  {conversation_id: {user_id, messages[]}}
_conversations: Dict[str, Dict[str, Any]] = {}

CHAT_SYSTEM_PROMPT = """You are DevCareer Coach — a brutally honest but supportive AI career advisor.
You have access to the developer's complete GitHub audit data: code quality findings,
architecture analysis, career verdict, gap analysis, resume bullets, market intel,
and portfolio rankings.

RULES:
- Be specific and evidence-based. Cite repo names, file paths, and findings when relevant.
- Be concise but thorough. Use bullet points for lists.
- When the user asks about their code quality, reference specific findings from the audit.
- When asked about career advice, reference gap analysis and roadmap data.
- When asked about resume, reference the resume bullets and portfolio rankings.
- Be honest — don't sugarcoat. If their code has issues, say so with specific evidence.
- If you don't have information about something, say so clearly.
- Keep responses conversational and helpful, not robotic.
- Use markdown formatting (bold, lists, code blocks) for readability.
- When referencing a source, mention the repo name and type of insight.

You have been given CONTEXT below from the developer's audit data.
Use this context to answer the question. Do NOT make up information not in the context.

CONTEXT:
{context}

CONVERSATION HISTORY:
{history}
"""


def _build_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into a context string for the system prompt."""
    if not chunks:
        return "(No audit data available yet. The user needs to run an audit first.)"

    sections = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source_type = meta.get("type", "unknown")
        repo = meta.get("repo_name", "")
        relevance = chunk.get("relevance_score", 0)

        header = f"[Source {i} | type={source_type}"
        if repo:
            header += f" | repo={repo}"
        header += f" | relevance={relevance:.2f}]"

        sections.append(f"{header}\n{chunk['content']}")

    return "\n\n".join(sections)


def _build_history(messages: List[Dict[str, str]], max_turns: int = 10) -> str:
    """Format recent conversation history."""
    if not messages:
        return "(Start of conversation)"

    recent = messages[-max_turns * 2:]  # last N turns (user+assistant pairs)
    lines = []
    for msg in recent:
        role = msg["role"].upper()
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def _extract_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract source references from retrieved chunks for the response."""
    sources = []
    seen = set()
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        source_type = meta.get("type", "unknown")
        repo = meta.get("repo_name", "")
        source_key = meta.get("source", "")
        relevance = chunk.get("relevance_score", 0)

        # Deduplicate by source key
        dedup = f"{source_type}:{repo}:{source_key}"
        if dedup in seen:
            continue
        seen.add(dedup)

        # Build human-readable detail
        detail_map = {
            "finding": f"Code finding in {repo}" if repo else "Code finding",
            "module_summary": f"Architecture of {repo}" if repo else "Module summary",
            "onboarding": f"Onboarding path for {repo}" if repo else "Onboarding",
            "repo_score": f"Score for {repo}" if repo else "Repo score",
            "verdict": "Career verdict",
            "gap": "Gap analysis",
            "roadmap": "90-day roadmap",
            "resume": f"Resume bullet for {repo}" if repo else "Resume",
            "portfolio_rank": f"Portfolio ranking for {repo}" if repo else "Ranking",
            "market_intel": "Market intelligence",
            "job_match": "Job match",
            "activity": "Activity snapshot",
            "user_profile": "User profile",
        }
        detail = detail_map.get(source_type, source_type)

        sources.append({
            "type": source_type,
            "repo_name": repo or None,
            "detail": detail,
            "relevance": round(relevance, 3),
        })

    # Top 5 most relevant
    sources.sort(key=lambda s: s["relevance"], reverse=True)
    return sources[:5]


def _call_chat_llm(system_prompt: str, user_message: str, max_retries: int = 3) -> str:
    """
    Call the LLM for a conversational (non-JSON) response.
    Reuses the same LLM backend as claude_engine but expects plain text back.
    """
    client = _get_client()
    if not client:
        raise ValueError("LLM client not configured. Check OPENROUTER_API_KEY or LLM_PROVIDER settings.")

    create_kwargs = dict(
        model=get_llm_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.5,
        max_tokens=min(2048, _max_completion_tokens()),
    )

    response = None
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**create_kwargs)
            break
        except APITimeoutError as e:
            raise RuntimeError(f"Chat LLM timed out: {e}") from e
        except RateLimitError as e:
            last_error = e
            wait = 5 * (2 ** attempt)
            print(f"[chat_engine] Rate limited (attempt {attempt+1}/{max_retries}), retrying in {wait}s…")
            time.sleep(wait)
        except APIError as e:
            raise RuntimeError(f"Chat LLM API error: {e}") from e

    if response is None:
        raise RuntimeError(f"Chat LLM rate limited after {max_retries} attempts: {last_error}")

    if not response.choices:
        raise RuntimeError("Chat LLM returned no choices")

    raw = (response.choices[0].message.content or "").strip()
    raw = _strip_model_wrappers(raw)
    return raw


def get_or_create_conversation(
    conversation_id: Optional[str], user_id: str
) -> str:
    """Get existing conversation or create a new one."""
    if conversation_id and conversation_id in _conversations:
        conv = _conversations[conversation_id]
        if conv["user_id"] == user_id:
            return conversation_id

    # Create new
    new_id = str(uuid.uuid4())
    _conversations[new_id] = {
        "user_id": user_id,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "last_message_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "messages": [],
    }
    return new_id


def chat(
    user_id: str,
    message: str,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main chat entry point.
    1. Gets/creates conversation
    2. Retrieves relevant context from vector store
    3. Builds prompt with context + history
    4. Calls LLM
    5. Returns response with sources
    """
    # 1. Conversation management
    conv_id = get_or_create_conversation(conversation_id, user_id)
    conv = _conversations[conv_id]

    # 2. Retrieve relevant context
    chunks = vector_store.query(user_id, message, top_k=8)
    sources = _extract_sources(chunks)

    # 3. Build prompts
    context_str = _build_context(chunks)
    history_str = _build_history(conv["messages"])
    system = CHAT_SYSTEM_PROMPT.format(context=context_str, history=history_str)

    # 4. Call LLM (with intelligent fallback)
    try:
        response_text = _call_chat_llm(system, message)
    except Exception as e:
        # --- Fallback: generate response from retrieved context ---
        response_text = _generate_fallback_response(message, chunks)
        if not response_text:
            response_text = (
                f"I'm having trouble connecting to the AI service right now. "
                f"But I found {len(chunks)} relevant data points from your audit. "
                f"Please try again in a moment, or ask a more specific question."
            )
        sources = []

    # 5. Store in conversation history
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conv["messages"].append({"role": "user", "content": message, "timestamp": now})
    conv["messages"].append({"role": "assistant", "content": response_text, "timestamp": now})
    conv["last_message_at"] = now

    # Keep conversation history bounded (last 50 messages)
    if len(conv["messages"]) > 50:
        conv["messages"] = conv["messages"][-50:]

    return {
        "response": response_text,
        "conversation_id": conv_id,
        "sources": sources,
    }


def _generate_fallback_response(message: str, chunks: List[Dict[str, Any]]) -> Optional[str]:
    """Generate a helpful response from retrieved chunks when LLM is unavailable."""
    if not chunks:
        return (
            "I don't have any audit data for your profile yet. "
            "Please run an audit first by entering your GitHub username on the home page, "
            "then come back to chat about your results!"
        )

    msg_lower = message.lower()

    # Categorize retrieved chunks by type
    by_type: Dict[str, List[str]] = {}
    for chunk in chunks:
        ctype = chunk.get("metadata", {}).get("type", "unknown")
        by_type.setdefault(ctype, []).append(chunk["content"])

    # Build targeted response based on question keywords
    parts = []

    if any(kw in msg_lower for kw in ("resume", "bullet", "rewrite", "cv")):
        if "resume" in by_type:
            parts.append("**Resume Insights from Your Audit:**\n")
            for item in by_type["resume"][:3]:
                parts.append(f"- {item}\n")
        else:
            parts.append("I found audit data but no resume-specific insights. Try running a fresh audit.\n")

    elif any(kw in msg_lower for kw in ("gap", "block", "promotion", "improve", "weak")):
        if "gap" in by_type:
            parts.append("**Career Gaps Identified:**\n")
            for item in by_type["gap"][:4]:
                parts.append(f"- {item}\n")

    elif any(kw in msg_lower for kw in ("roadmap", "plan", "study", "learn", "week")):
        if "roadmap" in by_type:
            parts.append("**Your 90-Day Roadmap:**\n")
            for item in by_type["roadmap"][:6]:
                parts.append(f"- {item}\n")

    elif any(kw in msg_lower for kw in ("score", "quality", "repo", "code")):
        if "repo_score" in by_type or "finding" in by_type:
            parts.append("**Code Quality Insights:**\n")
            for item in (by_type.get("repo_score", []) + by_type.get("finding", []))[:4]:
                parts.append(f"- {item}\n")

    elif any(kw in msg_lower for kw in ("job", "role", "salary", "market", "hire")):
        if "market_intel" in by_type or "job_match" in by_type:
            parts.append("**Market & Job Insights:**\n")
            for item in (by_type.get("market_intel", []) + by_type.get("job_match", []))[:4]:
                parts.append(f"- {item}\n")

    elif any(kw in msg_lower for kw in ("verdict", "level", "junior", "mid", "senior")):
        if "verdict" in by_type:
            parts.append("**Your Career Verdict:**\n")
            for item in by_type["verdict"][:2]:
                parts.append(f"- {item}\n")

    # Generic fallback: show top relevant chunks
    if not parts:
        parts.append("Here's what I found from your audit data:\n\n")
        for chunk in chunks[:4]:
            parts.append(f"- {chunk['content'][:200]}\n")

    parts.append("\n\n*Note: AI service is currently unavailable. This response is generated from your cached audit data.*")
    return "".join(parts)


def get_conversation_history(conversation_id: str, user_id: str) -> Optional[List[Dict]]:
    """Get messages for a conversation (only if owned by user)."""
    conv = _conversations.get(conversation_id)
    if not conv or conv["user_id"] != user_id:
        return None
    return conv["messages"]


def delete_conversation(conversation_id: str, user_id: str) -> bool:
    """Delete a conversation."""
    conv = _conversations.get(conversation_id)
    if not conv or conv["user_id"] != user_id:
        return False
    del _conversations[conversation_id]
    return True


def list_conversations(user_id: str) -> List[Dict[str, Any]]:
    """List all conversations for a user."""
    result = []
    for conv_id, conv in _conversations.items():
        if conv["user_id"] != user_id:
            continue
        # Find first user message for preview
        preview = ""
        for msg in conv["messages"]:
            if msg["role"] == "user":
                preview = msg["content"][:80]
                break
        result.append({
            "conversation_id": conv_id,
            "created_at": conv["created_at"],
            "last_message_at": conv["last_message_at"],
            "message_count": len(conv["messages"]),
            "preview": preview or "(empty)",
        })
    result.sort(key=lambda c: c["last_message_at"], reverse=True)
    return result
