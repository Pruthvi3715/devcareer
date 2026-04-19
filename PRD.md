# DevCareer Product Requirements Document (PRD)
**Version**: 1.0 — Hackathon Build
**Hackathon**: DevClash 2026 — April 18–19, 2026 — 24 Hours
**Venue**: Dr. D.Y. Patil Institute of Technology, Pimpri
**Track**: Track B — Others
**AI Stack**: Claude Sonnet 4 (`claude-sonnet-4-20250514`) via Anthropic API
**Product Name**: DevCareer — Audit your code. Know your level.

---

## 1. Problem Statement
**Primary (PS5):** Developer Career Intelligence System
**Secondary (PS3):** Repository Architecture Navigator (baked in as a feature layer)

Developers consistently misjudge their own skill level. Resumes are written from self-perception rather than demonstrated ability, portfolios are curated to hide weaknesses, and career advice remains generic to the point of uselessness.

There is currently no tool that:
- Audits what a developer has actually built from their real code.
- Compares it honestly against the job market with traceable evidence.
- Tells them exactly what stands between them and the next level.
- Maps the architecture of their repos so judges and employers understand the project fast.

**DevCareer solves all four.** The PS3 architecture navigation layer is embedded as a feature — not a separate product — giving our PS5 submission greater depth than any competitor.

---

## 2. Product Overview

### 2.1 One-Line Pitch
Input a GitHub username → receive a brutally honest 360-degree audit of your demonstrated skill level, architecture quality, career gaps, job market fit, and a 90-day roadmap to the next bracket — all traced to actual lines of code.

### 2.2 Core Differentiator
Every competitor (DevRank, GitRanks, SonarQube) audits one dimension. DevCareer is the only tool that combines:
- Actual code quality audit with file + line-level evidence.
- Architecture graph (PS3 layer) showing structural quality visually.
- Career verdict with market benchmarking and salary gap analysis.
- Actionable resume rewrite based on what code actually shows.

### 2.3 Target User
Mid-level developers (1–4 years) preparing for job applications, promotion conversations, or seeking honest feedback on where they stand versus market expectations.

---

## 3. System Architecture

### 3.1 End-to-End Data Flow
The system operates as a six-layer pipeline:

| Layer | Component | What It Does | Tech Stack |
| :--- | :--- | :--- | :--- |
| **1** | User Input | GitHub username / repo URL / live app URL entered via React frontend. | React + FastAPI |
| **2** | Ingestion | GitHub API collector fetches all repos, commits, activity. Repo cloner walks file tree, detects languages, entry points. | PyGitHub, GitPython, tree-sitter |
| **3** | Analysis (parallel) | Static analysis (complexity, naming, test coverage, docs), Architecture mapper (dependency + call graph), Security scanner (hardcoded secrets, SQL injection, weak auth). | radon, pylint, bandit, semgrep, networkx, pydriller |
| **4** | AI Layer (Claude) | Three separate Claude API calls: Code Review Engine, Architecture Summarizer, Career Verdict Engine. Each receives specific context and returns structured JSON. | `claude-sonnet-4-20250514` |
| **5** | Market Intel | Job role matcher cross-references detected skills against live job postings. Salary & percentile engine places dev in tier among peers. | Adzuna API, Reed API, cached salary dataset |
| **6** | Output | Audit dashboard (skill verdict, repo scores, percentile rank), Architecture graph view (PS3 layer, interactive), Career report (90-day roadmap, resume rewrite, PDF export). | React, Recharts, React Flow, D3, PDF export |

### 3.2 Backend Folder Structure
```text
devcareer/
  backend/
    main.py               # FastAPI entry point
    routers/
      audit.py            # /audit endpoint — triggers full pipeline
      report.py           # /report/{id} — fetch cached results
    services/
      github_collector.py  # PyGitHub: fetch repos, commits, activity
      repo_parser.py       # GitPython + tree-sitter: clone & parse
      static_analyzer.py   # radon + pylint: complexity, naming, docs
      arch_mapper.py       # networkx: dependency + call graph (PS3)
      security_scanner.py  # bandit + semgrep: secrets, injection risks
      claude_engine.py     # All 3 Claude API calls
      market_intel.py      # Adzuna / Reed API + salary dataset
    models/
      audit_schema.py      # Pydantic schemas for all pipeline outputs
    cache/
      redis_client.py      # Cache audit results by username
  frontend/
    src/
      pages/
        AuditPage.jsx
      components/
        ArchGraph.jsx       # React Flow: interactive dep graph (PS3)
        CareerReport.jsx    # 90-day roadmap + resume bullets
        RepoScoreCard.jsx   # Per-repo audit card
        PercentileCard.jsx  # Peer ranking widget
```

---

## 4. Feature Requirements

### 4.1 Core — Must Ship
| Feature | Tier | Description | Owner / Tech |
| :--- | :--- | :--- | :--- |
| **GitHub Profile Ingestion** | CORE | Accepts GitHub username/URL, fetches all public repos via API v3. | PyGitHub, REST v3 |
| **Repo Cloning & Parsing** | CORE | Clones repos locally, detects languages, maps file tree & modules (feeds analysis + PS3 graph). | GitPython, tree-sitter |
| **Activity Snapshot** | CORE | Commit frequency, contribution graph, active vs dead repos. | GitHub API |
| **Static Code Analysis** | CORE | Cyclomatic complexity, naming conventions, function length, modularity score per file. | radon, pylint |
| **Security Anti-pattern Detection** | CORE | Hardcoded secrets, SQL injection risks, exposed API keys, weak auth patterns. | bandit, semgrep |
| **Architecture Graph (PS3)** | CORE | Dependency map, call graph, entry points, high-impact files highlighted. Core PS3 feature globally baked into PS5 audit. | networkx, pydriller |
| **AI Code Review per Repo** | CORE | Claude reads actual code, flags specific flaws with file + line-level evidence and severity. | Claude Sonnet 4 |
| **Test Coverage Estimation** | CORE | Detects test files, test frameworks used, rough coverage signal. | AST parser |
| **Documentation Completeness** | CORE | README quality, inline docstrings, API docs presence scored per repo. | AST + Claude |
| **Skill Level Verdict** | CORE | Junior / Mid / Senior verdict with specific evidence. | Claude Sonnet 4 |
| **Percentile Ranking** | CORE | Where the dev sits among peers with similar experience and stack. | Salary dataset |
| **Gap-to-Next-Level** | CORE | Exact skills blocking promotion, ranked by career ROI with specific fixes. | Claude Sonnet 4 |
| **90-Day Learning Roadmap** | CORE | Personalised plan attacking weakest points in order of career impact. | Claude Sonnet 4 |
| **Resume Bullet Rewriter** | CORE | Rewrites resume claims based on what code actually shows — not self-reported. | Claude Sonnet 4 |

### 4.2 Essential — Should Ship
| Feature | Tier | Description | Owner / Tech |
| :--- | :--- | :--- | :--- |
| **Role Qualification Check** | ESSENTIAL | Which roles (Junior / Mid / Senior / Staff) the dev qualifies for right now. | Claude + market data |
| **Stack-based Job Matching** | ESSENTIAL | Cross-references detected stack against current job postings. | Adzuna API, Reed API |
| **Salary Gap Identification** | ESSENTIAL | Which specific skills unlock the next salary bracket based on market data. | Cached salary dataset |
| **Repo Ranking** | ESSENTIAL | Scores each repo — which to lead with, which are hurting the profile. | Static analysis + Claude |
| **AI File Summaries (PS3)** | ESSENTIAL | Plain-English explanation of what each module does, generated per file. | Claude Sonnet 4 |
| **Onboarding Path (PS3)** | ESSENTIAL | Ordered read-list so judges or employers can understand the project fast. | networkx + Claude |

### 4.3 Additional — Nice to Have
| Feature | Tier | Description | Owner / Tech |
| :--- | :--- | :--- | :--- |
| **Lighthouse Audit** | ADDITIONAL | Performance, a11y, SEO scores via headless browser if live URL provided. | Playwright + Lighthouse CLI |
| **Responsiveness Check** | ADDITIONAL | Screenshot at mobile/tablet/desktop breakpoints, flags layout breaks. | Playwright CDP |
| **Architecture Evolution (PS3)**| ADDITIONAL | How repo structure changed over commits — shows growth or regression. | pydriller |
| **Orphaned Module Detection** | ADDITIONAL | Flags dead/unused files that add cognitive load without value. | networkx |
| **Codebase Q&A NLQ (PS3)** | ADDITIONAL | 'Where is auth handled?' → highlighted subgraph answer via Claude. | Claude Sonnet 4 |
| **Shareable Audit Report** | ADDITIONAL | One-click PDF/link export of the full audit to share with recruiters. | PDF export |

---

## 5. AI Prompt Engineering — Claude API
The system makes three separate Claude Sonnet 4 API calls. The prompts below are fine-tuned for structured JSON output, traceable evidence, and calibrated honesty.

### 5.1 Code Review Engine
**Context passed to Claude:** raw file content, static analysis metrics (complexity score, naming flags, coverage, docs) per file.
**Output:** structured JSON with findings, line citations, severity, and fixes.

```text
// PROMPT 1 — Code Review Engine (SYSTEM)
SYSTEM:
You are a senior software engineer conducting a formal code review.
Your job is to review the provided source files and return a structured
JSON audit. You must be specific, evidence-based, and calibrated.

RULES:
- Every finding MUST include: file name, line number(s), severity (critical/major/minor),
  a concrete description of the flaw, and a specific fix.
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
}

// PROMPT 1 — Code Review Engine (USER)
USER:
Review the following repository: {repo_name}

Static analysis metrics:
- Cyclomatic complexity avg: {complexity_avg}
- Naming violations: {naming_flags}
- Test file coverage signal: {test_coverage}%
- Documentation score: {doc_score}/100

Files to review (top {n} by impact score):

{file_1_name}:
...
{file_1_content}
...

{file_2_name}:
...
{file_2_content}
...

Return the JSON audit only. No preamble or explanation outside the JSON.
```

### 5.2 Architecture Summarizer (PS3 Layer)
**Context passed:** networkx dependency graph as JSON (nodes=files, edges=imports), entry points, high-impact files list.
**Output:** plain-English per-module summaries, onboarding path, optional NLQ answers.

```text
// PROMPT 2 — Architecture Summarizer (SYSTEM)
SYSTEM:
You are a senior developer writing onboarding documentation for a codebase.
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
- NLQ answer (if query provided): return a list of node IDs that are
  relevant to the query, with a one-sentence explanation each.

OUTPUT FORMAT (strict JSON):
{
  "module_summaries": {
    "src/auth/login.py": "Handles user login via JWT. Entry point for all authentication flows. CHANGE RISK: HIGH.",
    "src/utils/helpers.py": "ORPHANED — utility functions with no callers."
  },
  "onboarding_path": [
    { "order": 1, "file": "README.md", "reason": "Start here for..." },
    { "order": 2, "file": "src/main.py", "reason": "Entry point, wires..." }
  ],
  "nlq_answer": null
}

// PROMPT 2 — Architecture Summarizer (USER)
USER:
Repository: {repo_name}

Dependency graph (JSON):
{graph_json}

Entry points detected: {entry_points}

High-impact files (by centrality):
{high_impact_files}

Orphaned modules detected: {orphaned_modules}

Natural language query (null if none): {nlq_query}

Return the JSON output only. No markdown, no preamble.
```

### 5.3 Career Verdict Engine
**Context passed:** aggregated repo audits, activity summary, market data context.
**Output:** explicit Junior/Mid/Senior verdict, gap analysis tracked ROI, roadmap, and resume rewriting.

```text
// PROMPT 3 — Career Verdict Engine (SYSTEM)
SYSTEM:
You are a brutally honest senior engineering manager conducting a 360-degree
career audit for a developer. Your job is NOT to be encouraging.
Your job is to be accurate, specific, and useful.

You will receive a full audit of a developer's GitHub activity across all repos.
You must produce:
1. A skill level verdict (Junior / Mid / Senior) with a confidence score.
2. A gap analysis: the exact skills and patterns blocking promotion, ranked
   by career ROI (highest impact first). Each gap must cite specific evidence
   from the audit (file + line).
3. A 90-day roadmap: specific, ordered actions with estimated weekly effort.
   Each week block must address the highest-ROI gap first.
4. A resume bullet rewrite: for each repo, rewrite the developer's likely
   self-reported claim into an evidence-based bullet that a recruiter can verify.
5. Portfolio ranking: rank repos from 'lead with this' to 'hide this',
   with a one-sentence reason for each.

CALIBRATION RULES:
- Junior: < 2 years equivalent demonstrated quality, lacks patterns like proper error handling, testing, modular design.
- Mid: Writes working, readable code. May over-engineer. Tests exist but coverage is weak. No clear architectural thinking.
- Senior: Evidence of system design awareness, secure patterns, test coverage > 60%, documented APIs, clean boundaries.

EVIDENCE RULE: Every verdict claim MUST be traced to a specific finding.
Not: 'your auth is weak.' Required: 'In ProjectX/src/auth/login.py lines 42-45, you use == for password comparison instead of hmac.compare_digest...'.

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
      "promotion_impact": "Fixing this alone moves you from Junior to Mid on auth-heavy roles."
    }
  ],
  "roadmap_90_days": [
    { "week": "1-2", "focus": "Security patterns", "action": "...", "hours": 6 }
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
}

// PROMPT 3 — Career Verdict Engine (USER)
USER:
Developer GitHub: {github_username}
Years active on GitHub: {years_active}
Primary languages: {top_languages}

Activity summary:
- Total repos analyzed: {repo_count}
- Average commit frequency: {commit_freq} per month
- Dead repos (no commits > 6 months): {dead_repos}

Code audit findings across all repos:
{aggregated_findings_json}

Market context:
- Detected skill stack: {skill_stack}
- Market percentile estimate: {percentile}
- Roles qualifying for today: {qualifying_roles}
- Skills that unlock next salary bracket: {salary_unlock_skills}

Produce the full career audit JSON. No markdown. No preamble.
Every verdict claim must cite file + line evidence from the audit findings above.
```

---

## 6. UI/UX Live App Audit (Additional Feature)
Triggered only if the user provides a live application URL in addition to GitHub profile. Runs in parallel with the code audit pipeline.

| Requirement | Tool | Metric | Output |
| :--- | :--- | :--- | :--- |
| **Responsiveness** | Playwright CDP | `scrollWidth > innerWidth`, element overflow detection at 375/768/1440px | Pass/Fail per breakpoint + screenshot |
| **Accessibility** | axe-core + Lighthouse CLI | WCAG 2.1 score, missing ARIA tags, contrast ratios | Accessibility score 0-100 |
| **Load Times** | Lighthouse CLI | LCP, FCP, Time to Interactive (Core Web Vitals) | Performance score + CWV breakdown |
| **Animation Smoothness**| Chrome DevTools Protocol | FPS via performance trace, dropped frame count | Avg FPS, frame drop % |
| **Interaction Feedback**| Playwright + Web Vitals API | INP, visual state change on click/hover | INP ms, pass/fail per interaction |

### 6.1 Responsiveness Check Implementation
The automated sequence:
- Launch Playwright headless browser at Mobile (375×667), Tablet (768×1024), Desktop (1440×900).
- Inject JS to check `document.documentElement.scrollWidth > window.innerWidth`, check computed fonts < 12px.
- Capture full-page screenshot at each breakpoint via `page.screenshot({ fullPage: true })`.
- Use Resemble.js pixel-matching to detect severe rendering anomalies.

---

## 7. 24-Hour Build Order

| Window | Phase | What to Build | Done When |
| :--- | :--- | :--- | :--- |
| **10AM – 1PM** | Ingestion | GitHub API collector + repo cloner + parser. FastAPI `/audit` endpoint stub. | Can fetch repos + file tree for any public GitHub username |
| **1PM – 3PM** | Analysis Pipeline | Static analyzer (radon+pylint), Security scanner (bandit), Architecture mapper (networkx). | Can produce analysis JSON for a cloned repo |
| **3PM – 5PM** | Claude Calls | All 3 Claude API calls wired up. Prompts tuned for JSON output. | Can produce verdict + evidence JSON from real repo |
| **5PM – 6PM** | System Design Review | Prepare arch diagram for 1st Judging Round. Polish and present pipeline. | Architecture diagram + working API demo |
| **6PM – 9PM** | Frontend Core | React dashboard: skill verdict card, repo score cards, percentile widget. | End-to-end: input GitHub username → see verdict + gaps |
| **9PM – 12AM**| Market Intel + PS3 | Adzuna/Reed job matching. Architecture graph UI with React Flow. AI file summaries. | Architecture graph renders + job matches appear |
| **12AM – 3AM**| 2nd Judging Round Prep | Polish flows. Resume bullet rewriter. PDF export. Edge case handling. | Resume rewrite + PDF export working on test repos |
| **3AM – 7AM** | Essential Features | Repo ranking. NLQ codebase Q&A. Lighthouse audit if time permits. | Repo ranking + NLQ working. Stable on edge cases. |
| **7AM – 9AM** | Final Polish | Demo-ready UI. Smooth loading states. Test on 3-4 showcase profiles. | Demo video recorded. README written. Code pushed. |
| **9AM – 10AM**| Final Judging & Submit | Final judging round. Submit via portal before 10:00 AM sharp. | Submitted ✓ |

---

## 8. Judging Criteria Alignment
**DevClash 2026** criteria: Functional Correctness (80%) and Completeness (20%).

| Criterion | Weight | How DevCareer Addresses It |
| :--- | :--- | :--- |
| **Functional Correctness** | 80% | End-to-end pipeline works on any public GitHub URL. Verdict is specific and traceable. Hub/Architecture graph renders properly. Graceful error handling (rate limits, private repos). |
| **Completeness** | 20% | All CORE features ship. The baked-in PS3 architecture graph elevates completeness far beyond any pure-PS5 competitor. Layered scoping (Core → Essential → Additional) protects delivery targets. |

---

## 9. Environment Setup & API Keys

```bash
# .env — required before running
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...              # For higher API rate limits
ADZUNA_APP_ID=...                 # Free tier — job matching
ADZUNA_APP_KEY=...
REED_API_KEY=...                  # Free tier — UK job postings

# Optional
REDIS_URL=redis://localhost:6379  # Cache audit results
PLAYWRIGHT_HEADLESS=true          # For UI/UX audit (additional feature)
```

### 9.1 Rate Limit Strategy
- **GitHub API:** Authenticated requests give 5,000/hour (sufficient for up to 50 audits).
- **Claude API:** Batch files into chunks of 3-5 to safely clear the 200K context window limits.
- **Adzuna API:** Free tier 100 calls/day — cache job match results via hash of detected stack.
- **Redis Cache:** Store full audit payload for 1 hour by `github_username` to skip redundant demo processing.

---

## 10. Submission Checklist
All items required before **10:00 AM April 19, 2026**:

- [ ] Public GitHub repo with all commits timestamped after 10:00 AM April 18.
- [ ] `README.md` complete with setup guide, tech stack context, and `.env.example`.
- [ ] Working demo — deployed link OR 3-5 minute video walkthrough.
- [ ] Submission via official DevKraft portal.
- [ ] Pitch Deck (5-10 slides: problem, solution, architecture, demo, future scope) prepared.
- [ ] AI Tools properly disclosed (Claude via Anthropic API for all LLM analysis constraints).

*Disclose in submission form: Anthropic Claude `claude-sonnet-4-20250514` API used for code review, architecture summarization, and career verdict generation.*

**DevCareer — DevClash 2026 — DevKraft**
