from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class Finding(BaseModel):
    file: str
    lines: List[int]
    severity: str
    category: str
    finding: str
    fix: str

class RepoArchGraph(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class OnboardingStep(BaseModel):
    order: int
    file: str
    reason: str

class RepoScore(BaseModel):
    repo_name: str
    score: int
    findings: List[Finding]
    arch_graph: RepoArchGraph
    module_summaries: Dict[str, str]
    onboarding_path: List[OnboardingStep]

class ActivitySnapshot(BaseModel):
    repo_count: int
    commit_freq_per_month: float
    dead_repos: int
    top_languages: List[str]
    years_active: int

class GapAnalysis(BaseModel):
    gap: str
    career_roi: str
    evidence: str
    fix: str
    promotion_impact: str

class RoadmapStep(BaseModel):
    week: str
    focus: str
    action: str
    hours: int

class ResumeBullet(BaseModel):
    repo: str
    original_claim: str
    rewritten: str

class PortfolioRank(BaseModel):
    repo: str
    rank: int
    action: str
    reason: str

class CareerVerdict(BaseModel):
    verdict: str  # Junior | Mid | Senior
    confidence: float
    verdict_evidence: List[str]
    gap_analysis: List[GapAnalysis]
    roadmap_90_days: List[RoadmapStep]
    resume_bullets: List[ResumeBullet]
    portfolio_ranking: List[PortfolioRank]

class JobMatch(BaseModel):
    title: str
    company: str
    url: str
    match_score: int

class MarketIntel(BaseModel):
    percentile: int
    qualifying_roles: List[str]
    job_matches: List[JobMatch]
    salary_unlock_skills: List[str]

class AuditResult(BaseModel):
    audit_id: str
    github_username: str
    generated_at: str
    activity_snapshot: ActivitySnapshot
    repo_scores: List[RepoScore]
    career_verdict: CareerVerdict
    market_intel: MarketIntel
