from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi import Query
from cache.redis_client import get_cache, get_audit_status
from models.audit_schema import AuditResult

router = APIRouter()


def _norm_path(p: str) -> str:
    return (p or "").replace("\\", "/")

@router.get("/{audit_id}", response_model=AuditResult)
async def get_report(audit_id: str):
    """
    Returns cached full audit result once processing is complete.
    """
    result = get_cache(f"audit_{audit_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not found or still processing")
    return result

@router.get("/{audit_id}/status")
async def get_report_status(audit_id: str):
    """
    Polling endpoint for frontend progress indicator.
    """
    status = get_audit_status(audit_id)
    if not status:
        raise HTTPException(status_code=404, detail="Audit status not found")
    return status


@router.get("/{audit_id}/nlq")
async def nlq_search(
    audit_id: str,
    query: str = Query(..., min_length=1, max_length=200),
    repo: Optional[str] = Query(
        None,
        description="If set, only search this repository's graph (matches repo_name).",
    ),
):
    """
    Lightweight NLQ over the cached architecture graph.

    The backend does not retain full source code, so this endpoint provides
    a best-effort keyword match over repo graph node ids and module summaries.
    """
    result = get_cache(f"audit_{audit_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not found or still processing")

    q = query.strip().lower()
    tokens = [t for t in q.replace("?", " ").replace(",", " ").split() if t]
    if not tokens:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    repo_filter = repo.strip() if repo else None

    candidates = []
    for repo_row in (result.get("repo_scores") or []):
        repo_name = repo_row.get("repo_name", "unknown")
        if repo_filter and repo_name != repo_filter:
            continue
        arch = (repo_row.get("arch_graph") or {})
        nodes = arch.get("nodes") or []
        summaries = repo_row.get("module_summaries") or {}
        # Also match summary keys when paths differ only by separators
        summary_by_norm = {_norm_path(k): v for k, v in summaries.items()}

        for node in nodes:
            node_id = _norm_path(str(node.get("id", "")).strip())
            if not node_id:
                continue
            summary_text = summaries.get(node_id, "") or summary_by_norm.get(node_id, "")
            label = str(node.get("label", "") or "")
            hay = f"{node_id} {label} {summary_text}".lower()
            score = sum(1 for t in tokens if t in hay)
            if score > 0:
                candidates.append((score, repo_name, node_id, summary_text))

    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    top = candidates[:10]

    return {
        "query": query,
        "relevant_nodes": [
            {
                "repo": repo_name,
                "id": node_id,
                "match_score": score,
                "reason": (summary[:160] if summary else f"Matched keywords ({score})"),
            }
            for score, repo_name, node_id, summary in top
        ],
    }
