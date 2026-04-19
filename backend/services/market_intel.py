"""
Market Intelligence — Layer 5
PRD Section 4.1/4.2: Job role matching, salary gap identification, percentile ranking.
Uses Adzuna API with fallback mock data for hackathon.
"""
import os
import httpx
from typing import Dict, Any, List


# --- Salary dataset (cached/embedded for hackathon) ---
# Based on 2024-2025 developer salary data aggregated from public sources
SALARY_BRACKETS = {
    "Junior": {"min": 45000, "max": 75000, "median": 60000},
    "Mid": {"min": 70000, "max": 110000, "median": 90000},
    "Senior": {"min": 100000, "max": 160000, "median": 130000},
    "Staff": {"min": 140000, "max": 220000, "median": 180000},
}

# Skills that unlock salary brackets
SKILL_SALARY_MAP = {
    "System Design": {"bracket_unlock": "Senior", "salary_boost_pct": 15},
    "Kubernetes": {"bracket_unlock": "Senior", "salary_boost_pct": 12},
    "AWS": {"bracket_unlock": "Mid", "salary_boost_pct": 10},
    "React": {"bracket_unlock": "Mid", "salary_boost_pct": 8},
    "TypeScript": {"bracket_unlock": "Mid", "salary_boost_pct": 7},
    "GraphQL": {"bracket_unlock": "Mid", "salary_boost_pct": 6},
    "Docker": {"bracket_unlock": "Mid", "salary_boost_pct": 8},
    "CI/CD": {"bracket_unlock": "Senior", "salary_boost_pct": 10},
    "PostgreSQL": {"bracket_unlock": "Mid", "salary_boost_pct": 5},
    "Redis": {"bracket_unlock": "Senior", "salary_boost_pct": 7},
    "Machine Learning": {"bracket_unlock": "Senior", "salary_boost_pct": 18},
    "Security": {"bracket_unlock": "Senior", "salary_boost_pct": 14},
    "Testing/TDD": {"bracket_unlock": "Mid", "salary_boost_pct": 9},
}

# Role qualification matrix
ROLE_REQUIREMENTS = {
    "Junior Developer": {
        "min_repos": 2, "min_languages": 1, "max_complexity_avg": 15,
        "min_test_coverage": 0, "min_doc_score": 0,
    },
    "Mid-Level Developer": {
        "min_repos": 5, "min_languages": 2, "max_complexity_avg": 10,
        "min_test_coverage": 15, "min_doc_score": 30,
    },
    "Senior Developer": {
        "min_repos": 8, "min_languages": 3, "max_complexity_avg": 8,
        "min_test_coverage": 40, "min_doc_score": 60,
    },
    "Staff Engineer": {
        "min_repos": 12, "min_languages": 3, "max_complexity_avg": 6,
        "min_test_coverage": 60, "min_doc_score": 75,
    },
}


def get_market_intel(
    skill_stack: List[str],
    top_languages: List[str],
    years_active: int,
    repo_count: int,
    complexity_avg: float,
    test_coverage: float,
    doc_score: float,
) -> Dict[str, Any]:
    """
    Produces full market intelligence: percentile, qualifying roles,
    job matches, and salary unlock skills.
    """
    # --- Percentile ranking ---
    percentile = _compute_percentile(years_active, repo_count, complexity_avg, test_coverage)

    # --- Role qualification ---
    qualifying_roles = _check_role_qualification(
        repo_count, len(top_languages), complexity_avg, test_coverage, doc_score
    )

    # --- Salary unlock skills ---
    detected_skills_lower = {s.lower() for s in skill_stack}
    salary_unlock = []
    for skill, data in SKILL_SALARY_MAP.items():
        if skill.lower() not in detected_skills_lower:
            salary_unlock.append(skill)
    salary_unlock = salary_unlock[:5]  # Top 5 missing high-value skills

    # --- Job matches ---
    job_matches = _fetch_job_matches(skill_stack, top_languages)

    return {
        "percentile": percentile,
        "qualifying_roles": qualifying_roles,
        "job_matches": job_matches,
        "salary_unlock_skills": salary_unlock,
    }


def _compute_percentile(years: int, repos: int, complexity: float, test_cov: float) -> int:
    """Estimate developer percentile among peers."""
    score = 0
    # Repo count contribution (max 25)
    score += min(25, repos * 2.5)
    # Years contribution (max 20)
    score += min(20, years * 5)
    # Complexity (lower is better, max 30)
    if complexity <= 5:
        score += 30
    elif complexity <= 10:
        score += 20
    elif complexity <= 15:
        score += 10
    # Test coverage (max 25)
    score += min(25, test_cov * 0.5)

    return min(99, max(5, round(score)))


def _check_role_qualification(
    repo_count: int, lang_count: int, complexity: float, test_cov: float, doc_score: float
) -> List[str]:
    """Check which roles the developer qualifies for."""
    qualified = []
    for role, reqs in ROLE_REQUIREMENTS.items():
        if (repo_count >= reqs["min_repos"]
                and lang_count >= reqs["min_languages"]
                and complexity <= reqs["max_complexity_avg"]
                and test_cov >= reqs["min_test_coverage"]
                and doc_score >= reqs["min_doc_score"]):
            qualified.append(role)
    return qualified if qualified else ["Junior Developer"]


def _fetch_job_matches(skill_stack: List[str], languages: List[str]) -> List[Dict[str, Any]]:
    """Fetch job matches from Adzuna API or return mock data."""
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")

    if app_id and app_key:
        return _adzuna_search(skill_stack, languages, app_id, app_key)

    # Mock job data for hackathon demo
    search_terms = languages[:2] + skill_stack[:2]
    return [
        {
            "title": f"{lang} Developer",
            "company": company,
            "url": f"https://example.com/jobs/{i}",
            "match_score": max(60, 95 - i * 8),
        }
        for i, (lang, company) in enumerate(zip(
            search_terms,
            ["TechCorp", "StartupXYZ", "BigCo", "DevHouse"],
        ))
    ]


def _adzuna_search(
    skills: List[str], languages: List[str], app_id: str, app_key: str
) -> List[Dict[str, Any]]:
    """Real Adzuna API search."""
    query = " ".join(languages[:2] + skills[:2])
    url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 5,
        "content-type": "application/json",
    }

    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("results", [])[:5]:
            results.append({
                "title": r.get("title", "Unknown"),
                "company": r.get("company", {}).get("display_name", "Unknown"),
                "url": r.get("redirect_url", ""),
                "match_score": 80,
            })
        return results
    except Exception:
        return []
