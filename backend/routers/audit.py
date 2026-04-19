"""
/audit endpoint — triggers full pipeline
PRD Section 6.1: POST /audit → triggers Layers 1-5, returns audit_id
"""
import traceback
import uuid
import datetime
import threading
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel

from models.audit_schema import (
    AuditResult, ActivitySnapshot, RepoScore, CareerVerdict, MarketIntel,
    RepoArchGraph, OnboardingStep, Finding, GapAnalysis, RoadmapStep,
    ResumeBullet, PortfolioRank, JobMatch,
)
from cache.redis_client import set_cache, set_audit_status
from services import github_collector, repo_parser, static_analyzer
from services import arch_mapper, security_scanner, claude_engine, market_intel

router = APIRouter()


def _norm_repo_path(p: str) -> str:
    """Canonical file path for graph IDs, onboarding, and NLQ (forward slashes)."""
    return (p or "").replace("\\", "/").strip()


def _fallback_onboarding_path(arch_data: Dict[str, Any]) -> List[OnboardingStep]:
    """
    When the LLM returns no onboarding_path, derive steps from static graph signals
    (entry points + high-centrality files) so the UI is never empty for non-trivial graphs.
    """
    steps: List[OnboardingStep] = []
    order = 0
    seen: set[str] = set()

    for ep in (arch_data.get("entry_points") or [])[:8]:
        p = _norm_repo_path(ep if isinstance(ep, str) else str(ep))
        if not p or p in seen:
            continue
        seen.add(p)
        order += 1
        steps.append(
            OnboardingStep(
                order=order,
                file=p,
                reason="Entry point — start here for how the app or service boots.",
            )
        )

    for h in (arch_data.get("high_impact_files") or [])[:6]:
        if isinstance(h, dict):
            p = _norm_repo_path(h.get("file", ""))
            ind = int(h.get("in_degree", 0) or 0)
        else:
            p = _norm_repo_path(str(h))
            ind = 0
        if not p or p in seen:
            continue
        seen.add(p)
        order += 1
        reason = (
            f"High centrality ({ind} importers) — understand before large refactors."
            if ind
            else "Heavily imported module — important for system understanding."
        )
        steps.append(OnboardingStep(order=order, file=p, reason=reason))

    return steps


class AuditRequest(BaseModel):
    github_username: str


def process_audit_pipeline(audit_id: str, username: str):
    """
    Full pipeline: Ingestion → Analysis → AI Layer → Market Intel
    Each step updates progress so the frontend can poll /report/{id}/status
    """
    try:
        # =====================================================================
        # LAYER 2: Ingestion — GitHub API + Repo cloning
        # =====================================================================
        set_audit_status(audit_id, "processing", 5)

        github_data = github_collector.collect_user_data(username)
        activity = github_data["activity_snapshot"]
        repos_meta = github_data["repos"]

        set_audit_status(audit_id, "processing", 15)

        # =====================================================================
        # Process each repo through Layers 2-4
        # =====================================================================
        all_findings = []
        repo_scores = []
        repo_names = []

        # Limit to top 5 repos by star count for hackathon speed
        repos_to_analyze = sorted(repos_meta, key=lambda r: r.get("stars", 0), reverse=True)[:5]
        total_repos = len(repos_to_analyze)

        for idx, repo_meta in enumerate(repos_to_analyze):
            repo_name = repo_meta["name"]
            repo_names.append(repo_name)
            progress = 15 + int((idx / max(1, total_repos)) * 45)
            set_audit_status(audit_id, "processing", progress)

            local_path = None
            try:
                # --- Clone & Parse ---
                local_path = repo_parser.clone_repo(repo_meta["clone_url"], repo_name)
                parsed = repo_parser.parse_repo(local_path)

                if not parsed["files"]:
                    # Empty repo or no analyzable files
                    repo_scores.append(_empty_repo_score(repo_name))
                    continue

                # --- Layer 3: Static Analysis ---
                analysis = static_analyzer.analyze_repo(parsed)
                metrics = analysis["summary"]

                # --- Layer 3: Security Scan ---
                security = security_scanner.scan_repo(parsed)

                # --- Layer 3: Architecture Graph (PS3) ---
                arch_data = arch_mapper.build_architecture_graph(parsed)

                # Combine findings from static analysis + security
                repo_findings = security["findings"]
                all_findings.extend(repo_findings)

                # --- Layer 4: Claude Code Review ---
                code_files = [f for f in parsed["files"] if not f["is_test"]]
                try:
                    claude_review = claude_engine.code_review(
                        repo_name=repo_name,
                        complexity_avg=metrics["complexity_avg"],
                        naming_flags=metrics["naming_violations"],
                        test_coverage=metrics["test_coverage_signal"],
                        doc_score=metrics["doc_score"],
                        files=code_files,
                    )
                    if claude_review.get("error"):
                        raise ValueError(claude_review.get("error", "AI code review failed"))
                    # Merge Claude findings
                    claude_findings = claude_review.get("findings", [])
                    all_findings.extend(claude_findings)
                    repo_score_val = claude_review.get("repo_score", 50)
                except Exception as e:
                    claude_findings = []
                    repo_score_val = _compute_fallback_score(metrics)

                # --- Layer 4: Architecture Summarizer (PS3) ---
                try:
                    arch_summary = claude_engine.architecture_summarizer(
                        repo_name=repo_name,
                        graph_data=arch_data,
                    )
                    if arch_summary.get("error"):
                        raise ValueError(arch_summary.get("error", "AI architecture summary failed"))
                    module_summaries = arch_summary.get("module_summaries", {})
                    onboarding_path_raw = arch_summary.get("onboarding_path", [])
                except Exception:
                    module_summaries = {}
                    onboarding_path_raw = []

                # Build onboarding steps (normalize paths; fallback if LLM returns nothing usable)
                onboarding_path = [
                    OnboardingStep(
                        order=int(step.get("order", i + 1)),
                        file=_norm_repo_path(step.get("file", "")),
                        reason=str(step.get("reason", "") or ""),
                    )
                    for i, step in enumerate(onboarding_path_raw)
                ]
                if not onboarding_path or not any(s.file for s in onboarding_path):
                    onboarding_path = _fallback_onboarding_path(arch_data)

                # Build findings list
                combined_findings = [
                    Finding(
                        file=f.get("file", "unknown"),
                        lines=f.get("lines", []),
                        severity=f.get("severity", "minor"),
                        category=f.get("category", "general"),
                        finding=f.get("finding", ""),
                        fix=f.get("fix", ""),
                    )
                    for f in (repo_findings + claude_findings)
                ]

                repo_scores.append(RepoScore(
                    repo_name=repo_name,
                    score=repo_score_val,
                    findings=combined_findings,
                    arch_graph=RepoArchGraph(
                        nodes=arch_data.get("nodes", []),
                        edges=arch_data.get("edges", []),
                    ),
                    module_summaries=module_summaries,
                    onboarding_path=onboarding_path,
                ))

            except Exception as e:
                print(f"Error processing repo {repo_name}: {e}")
                traceback.print_exc()
                repo_scores.append(_empty_repo_score(repo_name))

            finally:
                # Cleanup cloned repo
                try:
                    if local_path:
                        repo_parser.cleanup_clone(local_path)
                except Exception:
                    pass

        # =====================================================================
        # LAYER 5: Market Intel
        # =====================================================================
        set_audit_status(audit_id, "processing", 65)

        market_data = market_intel.get_market_intel(
            skill_stack=activity["top_languages"],
            top_languages=activity["top_languages"],
            years_active=activity["years_active"],
            repo_count=activity["repo_count"],
            complexity_avg=_avg_metric(repo_scores, "score"),
            test_coverage=0,  # Aggregated later
            doc_score=0,
        )

        # =====================================================================
        # LAYER 4: Career Verdict Engine (needs all data)
        # =====================================================================
        set_audit_status(audit_id, "processing", 75)

        try:
            verdict_data = claude_engine.career_verdict(
                username=username,
                years_active=activity["years_active"],
                top_languages=activity["top_languages"],
                repo_count=activity["repo_count"],
                commit_freq=activity["commit_freq_per_month"],
                dead_repos=activity["dead_repos"],
                aggregated_findings=[
                    {"file": f.get("file", ""), "lines": f.get("lines", []),
                     "severity": f.get("severity", ""), "finding": f.get("finding", "")}
                    for f in all_findings
                ],
                skill_stack=activity["top_languages"],
                percentile=market_data["percentile"],
                qualifying_roles=market_data["qualifying_roles"],
                salary_unlock_skills=market_data["salary_unlock_skills"],
                repo_names=repo_names,
            )
            if verdict_data.get("error"):
                raise ValueError(verdict_data.get("error", "AI career verdict failed"))
        except Exception as e:
            print(f"Career verdict failed: {e}")
            verdict_data = _fallback_verdict()

        set_audit_status(audit_id, "processing", 90)

        # =====================================================================
        # Build final AuditResult
        # =====================================================================
        career = CareerVerdict(
            verdict=verdict_data.get("verdict", "Mid"),
            confidence=verdict_data.get("confidence", 0.5),
            verdict_evidence=verdict_data.get("verdict_evidence", []),
            gap_analysis=[
                GapAnalysis(**g) for g in verdict_data.get("gap_analysis", [])
            ],
            roadmap_90_days=[
                RoadmapStep(**r) for r in verdict_data.get("roadmap_90_days", [])
            ],
            resume_bullets=[
                ResumeBullet(**b) for b in verdict_data.get("resume_bullets", [])
            ],
            portfolio_ranking=[
                PortfolioRank(**p) for p in verdict_data.get("portfolio_ranking", [])
            ],
        )

        market_result = MarketIntel(
            percentile=market_data["percentile"],
            qualifying_roles=market_data["qualifying_roles"],
            job_matches=[JobMatch(**j) for j in market_data["job_matches"]],
            salary_unlock_skills=market_data["salary_unlock_skills"],
        )

        result = AuditResult(
            audit_id=audit_id,
            github_username=username,
            generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            activity_snapshot=ActivitySnapshot(**activity),
            repo_scores=repo_scores,
            career_verdict=career,
            market_intel=market_result,
        )

        set_cache(f"audit_{audit_id}", result.model_dump())

        # --- Vectorize audit data for the profile chatbot ---
        try:
            from services import vector_store
            doc_count = vector_store.ingest_audit_data(username, result.model_dump())
            print(f"[audit] Vectorized {doc_count} documents for chatbot (user: {username})")
        except Exception as ve:
            print(f"[audit] Vector ingestion failed (non-fatal): {ve}")

        set_audit_status(audit_id, "done", 100)

    except Exception as e:
        print(f"Pipeline failed for {username}: {e}")
        traceback.print_exc()
        set_audit_status(audit_id, "error", 0, message=str(e))


def _empty_repo_score(repo_name: str) -> RepoScore:
    return RepoScore(
        repo_name=repo_name,
        score=0,
        findings=[],
        arch_graph=RepoArchGraph(nodes=[], edges=[]),
        module_summaries={},
        onboarding_path=[],
    )


def _compute_fallback_score(metrics: dict) -> int:
    """Compute repo score without Claude."""
    score = 50
    if metrics.get("complexity_avg", 10) < 5:
        score += 15
    elif metrics.get("complexity_avg", 10) > 15:
        score -= 15
    if metrics.get("test_coverage_signal", 0) > 30:
        score += 10
    if metrics.get("doc_score", 0) > 50:
        score += 10
    if metrics.get("naming_violations", 0) == 0:
        score += 5
    return max(0, min(100, score))


def _avg_metric(repo_scores: list, field: str) -> float:
    if not repo_scores:
        return 0
    vals = [getattr(r, field, 0) for r in repo_scores]
    return sum(vals) / len(vals)


def _fallback_verdict() -> dict:
    return {
        "verdict": "Mid",
        "confidence": 0.5,
        "verdict_evidence": ["LLM unavailable — verdict based on static analysis only"],
        "gap_analysis": [],
        "roadmap_90_days": [],
        "resume_bullets": [],
        "portfolio_ranking": [],
    }


@router.post("", response_model=Dict[str, str])
@router.post("/", response_model=Dict[str, str])
async def trigger_audit(body: AuditRequest):
    """
    POST /audit — Triggers full pipeline for a GitHub username.
    Returns audit_id immediately, processes in background.
    If username is 'demo', returns the pre-seeded demo audit instantly.
    """
    clean_username = body.github_username.strip().lower()

    # --- Demo mode: return pre-seeded audit instantly ---
    if clean_username == "demo":
        from cache.demo_data import DEMO_AUDIT_ID
        return {"audit_id": DEMO_AUDIT_ID, "status": "done"}

    audit_id = str(uuid.uuid4())
    set_audit_status(audit_id, "processing", 0)

    # NOTE: FastAPI's BackgroundTasks runs inside the server process and can still
    # block responsiveness if the task is CPU / IO heavy. We start a daemon thread
    # so the API remains responsive during long-running audits.
    threading.Thread(
        target=process_audit_pipeline,
        args=(audit_id, body.github_username),
        daemon=True,
    ).start()

    return {"audit_id": audit_id, "status": "processing"}
