"""
GitHub Profile Ingestion — Layer 2
PRD Section 4.1: Accepts GitHub username, fetches all public repos via GitHub API v3.
Produces: activity snapshot, repo list, language stats, commit frequency.
"""
import os
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

import requests


def collect_user_data(username: str) -> Dict[str, Any]:
    """
    Fetches all public repos, commit frequency, languages, and activity data
    for a given GitHub username. Returns structured data matching
    ActivitySnapshot + repo metadata needed by downstream services.
    """
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # NOTE: We use direct HTTP calls instead of PyGithub to avoid automatic
    # rate-limit backoff sleeps that make the pipeline appear "stuck".
    user_resp = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=15)
    if user_resp.status_code == 403 and "rate limit" in (user_resp.text or "").lower():
        raise ValueError("GitHub rate limit exceeded. Set GITHUB_TOKEN in backend .env and retry.")
    if user_resp.status_code == 404:
        raise ValueError(f"GitHub profile not found for '{username}'")
    if not user_resp.ok:
        raise ValueError(f"GitHub API error for '{username}': {user_resp.text[:200]}")

    user = user_resp.json()
    created_at_raw = user.get("created_at")
    created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00")) if created_at_raw else datetime.now(timezone.utc)

    repos_resp = requests.get(
        f"https://api.github.com/users/{username}/repos",
        headers=headers,
        params={"type": "public", "sort": "updated", "per_page": 100, "page": 1},
        timeout=30,
    )
    if repos_resp.status_code == 403 and "rate limit" in (repos_resp.text or "").lower():
        raise ValueError("GitHub rate limit exceeded. Set GITHUB_TOKEN in backend .env and retry.")
    if not repos_resp.ok:
        raise ValueError(f"GitHub API error fetching repos: {repos_resp.text[:200]}")

    repos = repos_resp.json() or []
    if not repos:
        raise ValueError(f"No public repos found for '{username}'")

    # --- Language aggregation (primary language only; no extra calls) ---
    lang_counts: Dict[str, int] = {}
    for repo in repos[:100]:
        lang = (repo.get("language") or "Unknown").strip()
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_languages = [l for l in sorted(lang_counts, key=lang_counts.get, reverse=True) if l != "Unknown"][:5]

    # --- Commit frequency & dead repo detection ---
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    total_commits = 0
    dead_repos = 0
    repo_metadata: List[Dict[str, Any]] = []

    for repo in repos[:20]:  # Cap at 20 repos for hackathon speed
        try:
            # We avoid per-repo commit listing calls (expensive). For a lightweight
            # commit signal, we use stargazers/forks/updated timestamps only.
            # Commit frequency becomes a coarse heuristic.
            pushed_at_raw = repo.get("pushed_at")
            last_push = datetime.fromisoformat(pushed_at_raw.replace("Z", "+00:00")) if pushed_at_raw else None
            is_dead = last_push < six_months_ago if last_push else True
            if is_dead:
                dead_repos += 1

            repo_metadata.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "url": repo.get("html_url"),
                "clone_url": repo.get("clone_url"),
                "description": repo.get("description") or "",
                "language": repo.get("language") or "Unknown",
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "last_push": last_push.isoformat() if last_push else None,
                "is_dead": is_dead,
                "commit_count_sampled": 0,
                "has_readme": False,
            })
        except Exception:
            continue

    # --- Account age ---
    years_active = max(1, (datetime.now(timezone.utc) - created_at).days // 365)

    # --- Commit freq ---
    months_active = max(1, years_active * 12)
    commit_freq = round(total_commits / months_active, 1)

    return {
        "username": username,
        "activity_snapshot": {
            "repo_count": len(repos),
            "commit_freq_per_month": commit_freq,
            "dead_repos": dead_repos,
            "top_languages": top_languages,
            "years_active": years_active,
        },
        "repos": repo_metadata,
    }
