"""
Smoke-test the LLM stack (OpenRouter or Ollama) for all three AI layers:
code_review, architecture_summarizer, career_verdict.

Run from backend:
  cd devcareer/backend && python scripts/smoke_openrouter.py

- OpenRouter (default): set OPENROUTER_API_KEY and optional OPENROUTER_MODEL.
- Ollama: set LLM_PROVIDER=ollama, OLLAMA_MODEL (e.g. qwen2.5:latest), run `ollama serve`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env")


def main() -> int:
    from services import claude_engine as ce

    provider = ce.get_llm_provider()
    model = ce.get_llm_model()
    print(f"LLM_PROVIDER = {provider!r}", flush=True)
    print(f"LLM_MODEL = {model!r}", flush=True)

    if provider == "openrouter" and not os.getenv("OPENROUTER_API_KEY", "").strip():
        print("ERROR: OPENROUTER_API_KEY is empty. Set it in devcareer/backend/.env", flush=True)
        return 1
    if provider == "ollama":
        print("(Using Ollama; ensure `ollama serve` is running and the model is pulled.)", flush=True)

    # --- 1. code_review (minimal repo sample) ---
    print("\n=== code_review ===", flush=True)
    cr = ce.code_review(
        "smoke/test-repo",
        complexity_avg=2.0,
        naming_flags=0,
        test_coverage=5.0,
        doc_score=20.0,
        files=[
            {
                "path": "hello.py",
                "line_count": 12,
                "content": "def greet(name: str) -> str:\n    return f\"Hello, {name}\"\n",
            }
        ],
    )
    if cr.get("error"):
        print("FAIL:", cr.get("error"), cr.get("raw", "")[:400])
        return 1
    print("OK: keys", sorted(cr.keys()))
    assert "findings" in cr or "repo_score" in cr

    # --- 2. architecture_summarizer (tiny graph) ---
    print("\n=== architecture_summarizer ===")
    graph = {
        "nodes": ["main.py", "lib/util.py"],
        "edges": [["main.py", "lib/util.py"]],
    }
    arch = ce.architecture_summarizer(
        "smoke/test-repo",
        {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "entry_points": ["main.py"],
            "high_impact_files": ["lib/util.py"],
            "orphaned_modules": [],
        },
        nlq_query=None,
    )
    if arch.get("error"):
        print("FAIL:", arch.get("error"), arch.get("raw", "")[:400])
        return 1
    print("OK: keys", sorted(arch.keys()))

    # --- 3. career_verdict ---
    print("\n=== career_verdict ===")
    cv = ce.career_verdict(
        username="smoke_user",
        years_active=3,
        top_languages=["Python"],
        repo_count=2,
        commit_freq=4.0,
        dead_repos=0,
        aggregated_findings=[
            {
                "file": "hello.py",
                "lines": [1],
                "severity": "minor",
                "finding": "Example finding for smoke test.",
            }
        ],
        skill_stack=["Python"],
        percentile=50,
        qualifying_roles=["Backend Developer"],
        salary_unlock_skills=["system design"],
        repo_names=["smoke/test-repo", "other/legacy"],
    )
    if cv.get("error"):
        print("FAIL:", cv.get("error"), cv.get("raw", "")[:400])
        return 1
    print("OK: keys", sorted(cv.keys()))

    print("\nAll three AI paths returned parseable JSON.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
