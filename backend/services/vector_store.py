"""
Vector Store — ChromaDB integration for RAG-powered profile chatbot.
Chunks audit results into semantic documents, embeds them, and provides
similarity search for the chat engine.

Uses ChromaDB's built-in sentence-transformers embedding (all-MiniLM-L6-v2).
Zero external API cost, runs locally.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

# Persistent storage path
_CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_data")

_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    """Lazy-init the ChromaDB persistent client."""
    global _client
    if _client is None:
        os.makedirs(_CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=_CHROMA_DIR)
    return _client


def _collection_name(user_id: str) -> str:
    """Sanitize user_id into a valid ChromaDB collection name."""
    safe = user_id.replace("@", "_at_").replace(".", "_")
    # ChromaDB collection names: 3-63 chars, alphanumeric + underscores
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in safe)
    return f"user_{safe}"[:63]


def get_collection(user_id: str):
    """Get or create a per-user ChromaDB collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name=_collection_name(user_id),
        metadata={"hnsw:space": "cosine"},
    )


def _safe_str(val: Any) -> str:
    """Convert any value to a string safe for ChromaDB metadata."""
    if val is None:
        return ""
    if isinstance(val, (list, dict)):
        return json.dumps(val, separators=(",", ":"))
    return str(val)


def ingest_audit_data(user_id: str, audit_result: Dict[str, Any]) -> int:
    """
    Chunks a completed AuditResult into semantic documents and stores them.
    Returns the number of documents ingested.
    """
    collection = get_collection(user_id)

    documents: List[str] = []
    metadatas: List[Dict[str, str]] = []
    ids: List[str] = []

    audit_id = audit_result.get("audit_id", "unknown")
    github_username = audit_result.get("github_username", "unknown")
    doc_idx = 0

    def _add(text: str, meta: Dict[str, str]):
        nonlocal doc_idx
        if not text or not text.strip():
            return
        documents.append(text.strip())
        meta["audit_id"] = audit_id
        meta["github_username"] = github_username
        metadatas.append(meta)
        ids.append(f"{audit_id}_{doc_idx}")
        doc_idx += 1

    # --- Activity Snapshot ---
    activity = audit_result.get("activity_snapshot", {})
    if activity:
        text = (
            f"Activity snapshot for {github_username}: "
            f"{activity.get('repo_count', 0)} repositories, "
            f"{activity.get('commit_freq_per_month', 0):.1f} commits/month, "
            f"{activity.get('dead_repos', 0)} dead repos, "
            f"{activity.get('years_active', 0)} years active on GitHub. "
            f"Top languages: {', '.join(activity.get('top_languages', []))}."
        )
        _add(text, {"type": "activity", "source": "activity_snapshot"})

    # --- Repo Scores ---
    for repo in audit_result.get("repo_scores", []):
        repo_name = repo.get("repo_name", "unknown")

        # Per-finding documents
        for finding in repo.get("findings", []):
            text = (
                f"Code finding in {repo_name}/{finding.get('file', '?')}: "
                f"[{finding.get('severity', 'minor').upper()}] [{finding.get('category', 'general')}] "
                f"{finding.get('finding', '')} "
                f"Fix: {finding.get('fix', 'N/A')} "
                f"Lines: {finding.get('lines', [])}"
            )
            _add(text, {
                "type": "finding",
                "repo_name": repo_name,
                "severity": _safe_str(finding.get("severity")),
                "category": _safe_str(finding.get("category")),
                "source": f"{repo_name}/findings",
            })

        # Module summaries
        for module_path, summary in repo.get("module_summaries", {}).items():
            text = f"Module summary for {repo_name}/{module_path}: {summary}"
            _add(text, {
                "type": "module_summary",
                "repo_name": repo_name,
                "module_path": module_path,
                "source": f"{repo_name}/architecture",
            })

        # Onboarding path
        for step in repo.get("onboarding_path", []):
            text = (
                f"Onboarding step {step.get('order', '?')} for {repo_name}: "
                f"Read {step.get('file', '?')} — {step.get('reason', '')}"
            )
            _add(text, {
                "type": "onboarding",
                "repo_name": repo_name,
                "source": f"{repo_name}/onboarding",
            })

        # Repo score summary
        text = f"Repository {repo_name} scored {repo.get('score', 0)}/100 in code quality audit."
        _add(text, {
            "type": "repo_score",
            "repo_name": repo_name,
            "score": _safe_str(repo.get("score", 0)),
            "source": f"{repo_name}/score",
        })

    # --- Career Verdict ---
    verdict = audit_result.get("career_verdict", {})
    if verdict:
        text = (
            f"Career verdict for {github_username}: {verdict.get('verdict', 'Unknown')} "
            f"(confidence: {verdict.get('confidence', 0):.0%}). "
            f"Evidence: {'; '.join(verdict.get('verdict_evidence', []))}"
        )
        _add(text, {"type": "verdict", "source": "career_verdict"})

        # Gap analysis
        for gap in verdict.get("gap_analysis", []):
            text = (
                f"Career gap: {gap.get('gap', '')}. "
                f"ROI: {gap.get('career_roi', 'unknown')}. "
                f"Evidence: {gap.get('evidence', 'N/A')}. "
                f"Fix: {gap.get('fix', '')}. "
                f"Promotion impact: {gap.get('promotion_impact', '')}"
            )
            _add(text, {
                "type": "gap",
                "career_roi": _safe_str(gap.get("career_roi")),
                "source": "gap_analysis",
            })

        # Roadmap
        for step in verdict.get("roadmap_90_days", []):
            text = (
                f"90-day roadmap — Week {step.get('week', '?')}: "
                f"Focus on {step.get('focus', '')}. "
                f"Action: {step.get('action', '')}. "
                f"Estimated effort: {step.get('hours', 0)} hours."
            )
            _add(text, {
                "type": "roadmap",
                "week": _safe_str(step.get("week")),
                "source": "roadmap_90_days",
            })

        # Resume bullets
        for bullet in verdict.get("resume_bullets", []):
            text = (
                f"Resume for {bullet.get('repo', '?')}: "
                f"Original claim: \"{bullet.get('original_claim', '')}\". "
                f"Evidence-based rewrite: \"{bullet.get('rewritten', '')}\""
            )
            _add(text, {
                "type": "resume",
                "repo_name": _safe_str(bullet.get("repo")),
                "source": "resume_bullets",
            })

        # Portfolio ranking
        for rank in verdict.get("portfolio_ranking", []):
            text = (
                f"Portfolio rank #{rank.get('rank', '?')}: {rank.get('repo', '?')} — "
                f"Action: {rank.get('action', '')}. "
                f"Reason: {rank.get('reason', '')}"
            )
            _add(text, {
                "type": "portfolio_rank",
                "repo_name": _safe_str(rank.get("repo")),
                "source": "portfolio_ranking",
            })

    # --- Market Intel ---
    market = audit_result.get("market_intel", {})
    if market:
        text = (
            f"Market intelligence for {github_username}: "
            f"Percentile rank: {market.get('percentile', 0)}th among peers. "
            f"Qualifying roles: {', '.join(market.get('qualifying_roles', []))}. "
            f"Skills to unlock next salary bracket: {', '.join(market.get('salary_unlock_skills', []))}."
        )
        _add(text, {"type": "market_intel", "source": "market_intel"})

        for job in market.get("job_matches", []):
            text = (
                f"Job match: {job.get('title', '?')} at {job.get('company', '?')} — "
                f"Match score: {job.get('match_score', 0)}%. "
                f"URL: {job.get('url', 'N/A')}"
            )
            _add(text, {
                "type": "job_match",
                "source": "job_matches",
            })

    # --- Batch upsert ---
    if documents:
        # ChromaDB has a batch limit; chunk into groups of 100
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            end = min(i + batch_size, len(documents))
            collection.upsert(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
            )

    return len(documents)


def ingest_user_profile(user_id: str, profile: Dict[str, Any]) -> int:
    """Store user profile data as a searchable document."""
    collection = get_collection(user_id)

    skills = profile.get("skills", "") or ""
    job_level = profile.get("job_level", "") or ""
    company = profile.get("company", "") or ""
    language = profile.get("primary_language", "") or ""
    coding_style = profile.get("coding_style", "") or ""
    schooling = profile.get("schooling", "") or ""

    text = (
        f"User profile: Skills: {skills}. "
        f"Job level: {job_level}. Company: {company}. "
        f"Primary language: {language}. Coding style: {coding_style}. "
        f"Education: {schooling}."
    )

    if not text.strip():
        return 0

    collection.upsert(
        documents=[text],
        metadatas=[{"type": "user_profile", "source": "profile"}],
        ids=["profile_0"],
    )
    return 1


def query(user_id: str, question: str, top_k: int = 8) -> List[Dict[str, Any]]:
    """
    Semantic search over the user's vectorized data.
    Returns top_k most relevant chunks with metadata.
    """
    collection = get_collection(user_id)

    # Check if collection has any documents
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        distance = results["distances"][0][i] if results["distances"] else 1.0
        chunks.append({
            "content": doc,
            "metadata": meta,
            "relevance_score": round(1.0 - distance, 3),  # cosine: lower distance = more similar
        })

    return chunks


def delete_user_data(user_id: str) -> bool:
    """Delete all vectorized data for a user."""
    client = _get_client()
    try:
        client.delete_collection(_collection_name(user_id))
        return True
    except Exception:
        return False


def get_document_count(user_id: str) -> int:
    """Return the number of documents stored for a user."""
    try:
        collection = get_collection(user_id)
        return collection.count()
    except Exception:
        return 0
