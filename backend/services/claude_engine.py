"""
Claude AI Engine — Layer 4
PRD Section 5: Three LLM calls for code review, architecture summary, career verdict.

Backends (OpenAI-compatible HTTP API):
- **groq** (default): Groq LPU inference (fast, free tier).
- **openrouter**: cloud models via OpenRouter.
- **ollama**: local models via Ollama (`/v1` compatibility).

Set ``LLM_PROVIDER`` to choose backend. All prompts from PRD Section 5.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from . import token_optimizer

import httpx
from openai import APIError, APITimeoutError, OpenAI, RateLimitError


def get_llm_provider() -> str:
    """``gemini`` (default), ``groq``, ``openrouter``, or ``ollama``."""
    p = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if p in ("ollama", "local"):
        return "ollama"
    if p in ("groq",):
        return "groq"
    if p in ("gemini", "google"):
        return "gemini"
    return "openrouter"


def get_llm_model() -> str:
    """Active chat model id for the current provider."""
    provider = get_llm_provider()
    if provider == "ollama":
        return (os.getenv("OLLAMA_MODEL", "llama3.2") or "llama3.2").strip()
    if provider == "groq":
        return (os.getenv("GROQ_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b").strip()
    if provider == "gemini":
        return (os.getenv("GEMINI_MODEL", "gemini-2.0-flash") or "gemini-2.0-flash").strip()
    return (os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5") or "anthropic/claude-sonnet-4-5").strip()


def get_openrouter_model() -> str:
    """Backward-compatible alias for :func:`get_llm_model`."""
    return get_llm_model()


def _normalize_ollama_base(url: str) -> str:
    """Ensure OpenAI-compatible base URL ends with ``/v1``."""
    u = url.strip().rstrip("/")
    if u.endswith("/v1"):
        return u
    return f"{u}/v1"


def _ignore_system_proxy() -> bool:
    for key in (
        "LLM_IGNORE_SYSTEM_PROXY",
        "OPENROUTER_IGNORE_SYSTEM_PROXY",
        "OLLAMA_IGNORE_SYSTEM_PROXY",
    ):
        if os.getenv(key, "").strip().lower() in ("1", "true", "yes"):
            return True
    return False


def _make_http_client(read_sec: float) -> httpx.Client:
    connect_sec = min(30.0, read_sec)
    httpx_timeout = httpx.Timeout(
        connect=connect_sec,
        read=read_sec,
        write=connect_sec,
        pool=10.0,
    )
    return httpx.Client(timeout=httpx_timeout, trust_env=not _ignore_system_proxy())


def _max_completion_tokens() -> int:
    override = os.getenv("LLM_MAX_TOKENS", "").strip()
    if override:
        try:
            return max(256, min(32768, int(override)))
        except ValueError:
            pass
    provider = get_llm_provider()
    if provider == "ollama":
        try:
            return max(256, int(os.getenv("OLLAMA_MAX_TOKENS", "4096").strip() or "4096"))
        except ValueError:
            return 4096
    if provider == "groq":
        try:
            return max(256, int(os.getenv("GROQ_MAX_TOKENS", "8000").strip() or "8000"))
        except ValueError:
            return 8000
    try:
        return max(256, int(os.getenv("OPENROUTER_MAX_TOKENS", "8000").strip() or "8000"))
    except ValueError:
        return 8000


def _get_openrouter_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None
    referer = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost").strip()
    title = os.getenv("OPENROUTER_APP_TITLE", "DevCareer").strip()
    headers: Dict[str, str] = {}
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title
    read_sec = float(os.getenv("OPENROUTER_TIMEOUT", "240").strip() or "240")
    http_client = _make_http_client(read_sec)
    kwargs: Dict[str, Any] = dict(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        http_client=http_client,
        max_retries=1,
    )
    if headers:
        kwargs["default_headers"] = headers
    return OpenAI(**kwargs)


def _get_ollama_client() -> OpenAI:
    base = _normalize_ollama_base(
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip() or "http://127.0.0.1:11434"
    )
    api_key = (os.getenv("OLLAMA_API_KEY", "ollama") or "ollama").strip()
    read_sec = float(os.getenv("OLLAMA_TIMEOUT", "600").strip() or "600")
    http_client = _make_http_client(read_sec)
    return OpenAI(
        base_url=base,
        api_key=api_key,
        http_client=http_client,
        max_retries=0,
    )


def _get_groq_client() -> Optional[OpenAI]:
    """Groq LPU inference — OpenAI-compatible API."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    read_sec = float(os.getenv("GROQ_TIMEOUT", "120").strip() or "120")
    http_client = _make_http_client(read_sec)
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
        http_client=http_client,
        max_retries=1,
    )


def _get_gemini_client() -> Optional[OpenAI]:
    """Google Gemini — OpenAI-compatible API endpoint."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    read_sec = float(os.getenv("GEMINI_TIMEOUT", "240").strip() or "240")
    http_client = _make_http_client(read_sec)
    return OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=api_key,
        http_client=http_client,
        max_retries=1,
    )


def _get_client() -> Optional[OpenAI]:
    """OpenAI SDK client for the configured provider."""
    provider = get_llm_provider()
    if provider == "ollama":
        return _get_ollama_client()
    if provider == "groq":
        return _get_groq_client()
    if provider == "gemini":
        return _get_gemini_client()
    return _get_openrouter_client()


def llm_backend_label() -> str:
    """Human-readable backend name for errors and logs."""
    provider = get_llm_provider()
    return f"{provider}:{get_llm_model()}"


# Strip blocks some models emit before JSON (breaks json.loads).
_THINK_STRIP_PATTERNS = (
    r"<think>.*?</think>",
    r"<thinking>.*?</thinking>",
    r"<redacted_reasoning>.*?</redacted_reasoning>",
)


def _strip_model_wrappers(text: str) -> str:
    """Remove common model 'thinking' wrappers that break JSON parsing."""
    text = text.strip()
    for pat in _THINK_STRIP_PATTERNS:
        text = re.sub(pat, "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def _parse_model_json(raw: str) -> Dict[str, Any]:
    """Parse strict JSON; on failure try extracting the outermost {...} block."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    def _try_load(s: str) -> Optional[Dict[str, Any]]:
        try:
            out = json.loads(s)
            return out if isinstance(out, dict) else None
        except json.JSONDecodeError:
            return None

    fixed = raw
    # Common local-model glitch: extra "{" after "[" in array-of-objects
    fixed = re.sub(r"\[\s*\{\s*\{", "[{", fixed)

    for candidate in (raw, fixed):
        parsed = _try_load(candidate)
        if parsed is not None:
            return parsed

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end > start:
        snippet = raw[start : end + 1]
        snippet = re.sub(r"\[\s*\{\s*\{", "[{", snippet)
        parsed = _try_load(snippet)
        if parsed is not None:
            return parsed

    return {"error": "Failed to parse Claude response as JSON", "raw": raw[:500]}


import random
import threading

# ── Per-minute rate tracker ──────────────────────────────────────────────
# Tracks timestamps of requests to detect when we're approaching limits.
_request_log: list[float] = []
_request_log_lock = threading.Lock()
_RATE_WINDOW_SEC = 60  # sliding window
_RATE_SOFT_LIMIT = int(os.getenv("LLM_RATE_SOFT_LIMIT", "25"))  # proactive slowdown threshold


def _record_request() -> None:
    """Log a request timestamp for rate tracking."""
    now = time.time()
    with _request_log_lock:
        _request_log.append(now)
        # Prune entries older than window
        cutoff = now - _RATE_WINDOW_SEC
        while _request_log and _request_log[0] < cutoff:
            _request_log.pop(0)


def _requests_in_window() -> int:
    """Count requests in the current sliding window."""
    now = time.time()
    cutoff = now - _RATE_WINDOW_SEC
    with _request_log_lock:
        return sum(1 for t in _request_log if t >= cutoff)


def _proactive_cooldown() -> None:
    """If we're near the soft rate limit, sleep briefly before sending."""
    count = _requests_in_window()
    if count >= _RATE_SOFT_LIMIT:
        cooldown = 2.0 + random.uniform(0.5, 2.0)
        print(f"[claude_engine] Proactive cooldown: {count} reqs in last 60s (limit={_RATE_SOFT_LIMIT}), waiting {cooldown:.1f}s")
        time.sleep(cooldown)


def _call_claude(system_prompt: str, user_prompt: str, max_retries: int = 5) -> Dict[str, Any]:
    """Make a single LLM chat completion; response must be JSON. Returns parsed dict.

    Enhanced retry engine:
      - Adaptive exponential backoff with random jitter (prevents thundering herd).
      - Proactive per-minute rate tracking to slow down before hitting limits.
      - Configurable via LLM_MAX_RETRIES env var.
    """
    max_retries = int(os.getenv("LLM_MAX_RETRIES", str(max_retries)))

    client = _get_client()
    if not client:
        if get_llm_provider() == "ollama":
            raise ValueError(
                "LLM_PROVIDER=ollama but Ollama client could not be created. "
                "Check OLLAMA_BASE_URL and that `ollama serve` is running."
            )
        raise ValueError("OPENROUTER_API_KEY not set in environment")

    backend = llm_backend_label()
    create_kwargs: Dict[str, Any] = dict(
        model=get_llm_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=_max_completion_tokens(),
    )
    # Ollama OpenAI API: JSON mode reduces malformed braces in long schemas.
    if get_llm_provider() == "ollama":
        create_kwargs["response_format"] = {"type": "json_object"}

    # Proactive cooldown based on recent request rate
    _proactive_cooldown()

    response = None
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            _record_request()
            response = client.chat.completions.create(**create_kwargs)
            break  # success
        except APITimeoutError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = min(60, 3 * (2 ** attempt)) + random.uniform(0.5, 2.0)
                print(f"[claude_engine] Timeout (attempt {attempt+1}/{max_retries}), retrying in {wait:.1f}s…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"{backend} request timed out after {max_retries} attempts: {e}") from e
        except RateLimitError as e:
            last_error = e
            # Adaptive backoff: base * 2^attempt + random jitter
            base_wait = 5 * (2 ** attempt)  # 5, 10, 20, 40, 80
            jitter = random.uniform(1.0, 4.0)
            wait = min(120, base_wait + jitter)  # cap at 2 minutes
            print(f"[claude_engine] Rate limited (attempt {attempt+1}/{max_retries}), retrying in {wait:.1f}s…")
            time.sleep(wait)
        except APIError as e:
            if (
                get_llm_provider() == "ollama"
                and create_kwargs.pop("response_format", None) is not None
            ):
                try:
                    _record_request()
                    response = client.chat.completions.create(**create_kwargs)
                    break
                except APIError as e2:
                    raise RuntimeError(f"{backend} API error: {e2}") from e2
            else:
                raise RuntimeError(f"{backend} API error: {e}") from e

    if response is None:
        raise RuntimeError(f"{backend} rate limited after {max_retries} attempts: {last_error}") from last_error

    if not response.choices:
        raise RuntimeError(f"{backend} returned no choices")
    msg = response.choices[0].message
    raw = (msg.content or "").strip()
    if not raw:
        raise RuntimeError(f"{backend} returned empty message content")

    raw = _strip_model_wrappers(raw)
    return _parse_model_json(raw)


# =============================================================================
# PROMPT 1 — Code Review Engine (PRD Section 5.1)
# =============================================================================

CODE_REVIEW_SYSTEM = """You are a senior software engineer conducting a formal code review.
Your job is to review the provided source files and return a structured
JSON audit. You must be specific, evidence-based, and calibrated.

RULES:
- Every finding MUST include: file name, line number(s), severity
  (critical/major/minor), a concrete description of the flaw, and a specific fix.
- Do NOT give generic advice like 'improve naming' without citing exact examples.
- Do NOT give praise unless it is specific and evidence-backed.
- Severity calibration:
  critical = security risk or logic error that would fail code review at any company
  major    = architectural flaw or pattern that signals junior-level thinking
  minor    = style or readability issue that a senior would note in a PR comment
- If test coverage is below 20%, always flag it as major.
- If no README or docstrings exist, flag as major.

OUTPUT FORMAT (strict JSON, no markdown wrapping):
{
  "findings": [
    {
      "file": "src/auth/login.py",
      "lines": [42, 45],
      "severity": "critical",
      "category": "security",
      "finding": "Password comparison uses == instead of hmac.compare_digest, making this vulnerable to timing attacks.",
      "fix": "Replace == with hmac.compare_digest(stored_hash, computed_hash). See Python docs section 15.2."
    }
  ],
  "repo_score": 62,
  "summary": "2 critical, 4 major, 7 minor issues found across 12 files."
}"""


def code_review(
    repo_name: str,
    complexity_avg: float,
    naming_flags: int,
    test_coverage: float,
    doc_score: float,
    files: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """PRD Prompt 1 — Code Review Engine."""
    # Token Optimization: Filter, semantic ranking, and minify
    optimized_files = token_optimizer.optimize_code_review_payload(files, max_tokens=60000)

    file_sections = []
    for f in optimized_files:
        content = f["content"]
        file_sections.append(f"{f['path']}:\n```\n{content}\n```")

    user_prompt = f"""Review the following repository: {repo_name}

Static analysis metrics:
- Cyclomatic complexity avg: {complexity_avg}
- Naming violations: {naming_flags}
- Test file coverage signal: {test_coverage}%
- Documentation score: {doc_score}/100

Files to review (top {len(optimized_files)} by impact score):

{chr(10).join(file_sections)}

Return the JSON audit only. No preamble or explanation outside the JSON."""

    return _call_claude(CODE_REVIEW_SYSTEM, user_prompt)


# =============================================================================
# PROMPT 2 — Architecture Summarizer (PRD Section 5.2)
# =============================================================================

ARCH_SUMMARIZER_SYSTEM = """You are a senior developer writing onboarding documentation for a codebase.
You have been given a dependency graph of the repository as structured JSON.
Your job is to produce: (1) a plain-English summary for every module node,
(2) a recommended onboarding path for a new developer, and optionally
(3) an answer to a natural language query about the codebase.

RULES:
- Summaries must be 1-2 sentences maximum per module. No jargon.
- The onboarding path must be an ordered list. Start from entry points.
  Each step must explain WHY this file should be read at this point.
- High-impact files (high in-degree centrality) must be flagged as
  'CHANGE RISK: HIGH — affects N modules' in their summary.
- Orphaned nodes (no in-edges, no out-edges) must be flagged as
  'ORPHANED — may be unused, verify before deleting.'
- NLQ answer (if query provided): return a list of node IDs relevant
  to the query, with a one-sentence explanation each.

OUTPUT FORMAT (strict JSON):
{
  "module_summaries": {
    "src/auth/login.py": "Handles user login via JWT. Entry point for all authentication flows. CHANGE RISK: HIGH — affects 8 modules.",
    "src/utils/helpers.py": "ORPHANED — utility functions with no callers."
  },
  "onboarding_path": [
    { "order": 1, "file": "README.md", "reason": "Start here for project overview." },
    { "order": 2, "file": "src/main.py", "reason": "Entry point, wires all services." }
  ],
  "nlq_answer": null
}"""


def architecture_summarizer(
    repo_name: str,
    graph_data: Dict[str, Any],
    nlq_query: Optional[str] = None,
) -> Dict[str, Any]:
    """PRD Prompt 2 — Architecture Summarizer (PS3 Layer)."""
    entry_points = graph_data.get("entry_points", [])
    high_impact = graph_data.get("high_impact_files", [])
    orphaned = graph_data.get("orphaned_modules", [])

    # Serialize and optimize graph representation for the prompt
    graph_json = token_optimizer.optimize_architecture_graph(graph_data, max_tokens=15000)

    user_prompt = f"""Repository: {repo_name}
Dependency graph (JSON): {graph_json}
Entry points detected: {json.dumps(entry_points)}
High-impact files (by centrality): {json.dumps(high_impact)}
Orphaned modules detected: {json.dumps(orphaned)}
Natural language query (null if none): {json.dumps(nlq_query)}

Return the JSON output only. No markdown, no preamble."""

    return _call_claude(ARCH_SUMMARIZER_SYSTEM, user_prompt)


# =============================================================================
# PROMPT 3 — Career Verdict Engine (PRD Section 5.3)
# =============================================================================

CAREER_VERDICT_SYSTEM = """You are a brutally honest senior engineering manager conducting a 360-degree
career audit for a developer. Your job is NOT to be encouraging.
Your job is to be accurate, specific, and useful.

You must produce:
1. A skill level verdict (Junior / Mid / Senior) with a confidence score.
2. A gap analysis: exact skills and patterns blocking promotion, ranked by
   career ROI (highest impact first). Each gap must cite specific evidence
   from the audit (file + finding).
3. A 90-day roadmap: specific, ordered actions with estimated weekly effort.
   Each week block must address the highest-ROI gap first.
4. A resume bullet rewrite: for each repo, rewrite the developer's likely
   self-reported claim into an evidence-based bullet a recruiter can verify.
5. Portfolio ranking: rank repos from 'lead with this' to 'hide this',
   with a one-sentence reason for each.

CALIBRATION RULES:
- Junior: < 2 years equivalent demonstrated quality, lacks patterns like
  proper error handling, test writing, modular design.
- Mid: Writes working, readable code. May over-engineer. Tests exist but
  coverage is weak. No clear architectural thinking.
- Senior: Evidence of system design awareness, security-conscious patterns,
  test coverage > 60%, well-documented APIs, clean dependency boundaries.

EVIDENCE RULE: Every verdict claim MUST be traced to a specific finding.
Not: 'your auth is weak.'
Required: 'In ProjectX/src/auth/login.py lines 42-45, you use == for password
comparison instead of hmac.compare_digest — this is a timing attack
vulnerability that a senior engineer would reject immediately in code review.'

OUTPUT FORMAT (strict JSON):
{
  "verdict": "Junior",
  "confidence": 0.82,
  "verdict_evidence": ["Finding 1 with file+line citation", "..."],
  "gap_analysis": [
    {
      "gap": "Secure authentication patterns",
      "career_roi": "high",
      "evidence": "ProjectX/auth/login.py:42-45 — timing attack vulnerability",
      "fix": "Replace == with hmac.compare_digest. Read: OWASP Auth Cheatsheet.",
      "promotion_impact": "Fixing this alone moves you from Junior to Mid on auth-heavy roles at any company doing security review."
    }
  ],
  "roadmap_90_days": [
    { "week": "1-2", "focus": "Security patterns", "action": "...", "hours": 6 },
    { "week": "3-4", "focus": "Test coverage", "action": "...", "hours": 8 }
  ],
  "resume_bullets": [
    {
      "repo": "ProjectX",
      "original_claim": "Built a full-stack auth system",
      "rewritten": "Implemented JWT-based authentication for a Node/React app with 3 endpoints, session management, and bcrypt hashing (timing-attack vulnerability noted — not production-ready)."
    }
  ],
  "portfolio_ranking": [
    { "repo": "ProjectX", "rank": 1, "action": "lead_with", "reason": "..." },
    { "repo": "OldHack", "rank": 3, "action": "hide", "reason": "..." }
  ]
}"""


def career_verdict(
    username: str,
    years_active: int,
    top_languages: List[str],
    repo_count: int,
    commit_freq: float,
    dead_repos: int,
    aggregated_findings: List[Dict[str, Any]],
    skill_stack: List[str],
    percentile: int,
    qualifying_roles: List[str],
    salary_unlock_skills: List[str],
    repo_names: List[str],
) -> Dict[str, Any]:
    """PRD Prompt 3 — Career Verdict Engine."""
    findings_json = json.dumps(aggregated_findings[:50], separators=(',', ':'))  # Cap and minify findings

    user_prompt = f"""Developer GitHub: {username}
Years active on GitHub: {years_active}
Primary languages: {', '.join(top_languages)}

Activity summary:
- Total repos analyzed: {repo_count}
- Average commit frequency: {commit_freq} per month
- Dead repos (no commits > 6 months): {dead_repos}

Code audit findings across all repos:
{findings_json}

Market context:
- Detected skill stack: {', '.join(skill_stack)}
- Market percentile estimate: {percentile}
- Roles qualifying for today: {', '.join(qualifying_roles)}
- Skills that unlock next salary bracket: {', '.join(salary_unlock_skills)}

Repos analyzed: {', '.join(repo_names)}

Produce the full career audit JSON. No markdown. No preamble.
Every verdict claim must cite file + line evidence from the audit findings above."""

    return _call_claude(CAREER_VERDICT_SYSTEM, user_prompt)
