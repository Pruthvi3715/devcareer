"""
Pre-built demo audit result for DevCareer.
Loaded on startup so the app works without API keys or real GitHub data.
"""

DEMO_AUDIT_ID = "demo-audit-001"
DEMO_USERNAME = "demo"

DEMO_AUDIT_RESULT = {
    "audit_id": DEMO_AUDIT_ID,
    "github_username": DEMO_USERNAME,
    "generated_at": "2026-04-19T03:00:00Z",
    "activity_snapshot": {
        "repo_count": 12,
        "commit_freq_per_month": 14.3,
        "dead_repos": 3,
        "top_languages": ["Python", "JavaScript", "TypeScript", "Go"],
        "years_active": 4,
    },
    "repo_scores": [
        {
            "repo_name": "ecommerce-api",
            "score": 72,
            "findings": [
                {
                    "file": "src/auth/handler.py",
                    "lines": [31, 35],
                    "severity": "critical",
                    "category": "security",
                    "finding": "Password comparison uses == instead of hmac.compare_digest, vulnerable to timing attacks.",
                    "fix": "Replace == with hmac.compare_digest(stored_hash, computed_hash).",
                },
                {
                    "file": "src/orders/service.py",
                    "lines": [88, 95],
                    "severity": "major",
                    "category": "error-handling",
                    "finding": "Bare except clause swallows all exceptions including SystemExit and KeyboardInterrupt.",
                    "fix": "Replace 'except:' with 'except Exception as e:' and log the error.",
                },
                {
                    "file": "src/models/product.py",
                    "lines": [12],
                    "severity": "minor",
                    "category": "naming",
                    "finding": "Variable 'x' is non-descriptive in a domain model.",
                    "fix": "Rename to 'product_discount_rate' or similar descriptive name.",
                },
            ],
            "arch_graph": {
                "nodes": [
                    {"id": "src/main.py", "label": "main.py", "type": "entry"},
                    {"id": "src/auth/handler.py", "label": "handler.py", "type": "module"},
                    {"id": "src/orders/service.py", "label": "service.py", "type": "module"},
                    {"id": "src/models/product.py", "label": "product.py", "type": "model"},
                ],
                "edges": [
                    {"source": "src/main.py", "target": "src/auth/handler.py"},
                    {"source": "src/main.py", "target": "src/orders/service.py"},
                    {"source": "src/orders/service.py", "target": "src/models/product.py"},
                ],
            },
            "module_summaries": {
                "src/main.py": "FastAPI application entry point. Wires auth, orders, and product routes.",
                "src/auth/handler.py": "Handles user authentication with JWT tokens. CHANGE RISK: HIGH — affects 4 modules.",
                "src/orders/service.py": "Order processing pipeline with Stripe payment integration.",
                "src/models/product.py": "SQLAlchemy ORM model for products with pricing logic.",
            },
            "onboarding_path": [
                {"order": 1, "file": "README.md", "reason": "Project overview and setup instructions."},
                {"order": 2, "file": "src/main.py", "reason": "Entry point — understand how routes are wired."},
                {"order": 3, "file": "src/auth/handler.py", "reason": "Auth is the first thing users hit."},
            ],
        },
        {
            "repo_name": "react-dashboard",
            "score": 58,
            "findings": [
                {
                    "file": "src/components/Chart.tsx",
                    "lines": [22, 45],
                    "severity": "major",
                    "category": "performance",
                    "finding": "useEffect runs on every render due to missing dependency array, causing infinite re-renders.",
                    "fix": "Add dependency array: useEffect(() => { ... }, [data]).",
                },
                {
                    "file": "src/App.tsx",
                    "lines": [5],
                    "severity": "major",
                    "category": "testing",
                    "finding": "Zero test files detected. No unit or integration tests across 18 components.",
                    "fix": "Add Jest + React Testing Library. Start with critical paths: auth flow, data fetching hooks.",
                },
                {
                    "file": "src/hooks/useAuth.ts",
                    "lines": [15, 20],
                    "severity": "critical",
                    "category": "security",
                    "finding": "JWT token stored in localStorage. Vulnerable to XSS attacks.",
                    "fix": "Use httpOnly cookies for token storage. Set SameSite=Strict and Secure flags.",
                },
            ],
            "arch_graph": {
                "nodes": [
                    {"id": "src/App.tsx", "label": "App.tsx", "type": "entry"},
                    {"id": "src/components/Chart.tsx", "label": "Chart.tsx", "type": "component"},
                    {"id": "src/hooks/useAuth.ts", "label": "useAuth.ts", "type": "hook"},
                ],
                "edges": [
                    {"source": "src/App.tsx", "target": "src/components/Chart.tsx"},
                    {"source": "src/App.tsx", "target": "src/hooks/useAuth.ts"},
                ],
            },
            "module_summaries": {
                "src/App.tsx": "React SPA entry point with React Router v6. Renders dashboard layout.",
                "src/components/Chart.tsx": "Recharts-based analytics chart with performance issue.",
                "src/hooks/useAuth.ts": "Authentication hook managing JWT lifecycle. CHANGE RISK: HIGH.",
            },
            "onboarding_path": [
                {"order": 1, "file": "src/App.tsx", "reason": "Entry point for the React SPA."},
                {"order": 2, "file": "src/hooks/useAuth.ts", "reason": "Auth logic affects all protected routes."},
            ],
        },
        {
            "repo_name": "cli-toolbox",
            "score": 45,
            "findings": [
                {
                    "file": "main.go",
                    "lines": [10, 88],
                    "severity": "major",
                    "category": "architecture",
                    "finding": "Entire application logic in a single 400-line file with no package structure.",
                    "fix": "Split into packages: cmd/, internal/parser/, internal/formatter/.",
                },
                {
                    "file": "main.go",
                    "lines": [120, 135],
                    "severity": "minor",
                    "category": "error-handling",
                    "finding": "Error from os.ReadFile ignored with _ assignment.",
                    "fix": "Handle error: if err != nil { log.Fatalf(...) }.",
                },
            ],
            "arch_graph": {
                "nodes": [{"id": "main.go", "label": "main.go", "type": "entry"}],
                "edges": [],
            },
            "module_summaries": {
                "main.go": "Monolithic CLI tool. No package structure. All logic in one file.",
            },
            "onboarding_path": [
                {"order": 1, "file": "main.go", "reason": "Only file — entire application lives here."},
            ],
        },
    ],
    "career_verdict": {
        "verdict": "Mid",
        "confidence": 0.74,
        "verdict_evidence": [
            "In ecommerce-api/src/auth/handler.py lines 31-35, password comparison uses == instead of hmac.compare_digest — timing attack vulnerability that a senior would catch in code review.",
            "react-dashboard has 0% test coverage across 18 components — no evidence of testing discipline.",
            "cli-toolbox/main.go is a 400-line monolith with no package structure — lacks architectural thinking expected at Senior level.",
            "Positive: ecommerce-api shows understanding of REST API patterns and clean route organization (score 72/100).",
            "14.3 commits/month over 4 years shows consistent coding activity — not a weekend warrior.",
        ],
        "gap_analysis": [
            {
                "gap": "Security-conscious authentication patterns",
                "career_roi": "high",
                "evidence": "ecommerce-api/src/auth/handler.py:31-35 — timing attack vulnerability; react-dashboard/src/hooks/useAuth.ts:15-20 — JWT in localStorage",
                "fix": "Study OWASP Auth Cheatsheet. Replace == with hmac.compare_digest. Move JWT to httpOnly cookies. Add CSRF tokens.",
                "promotion_impact": "Fixing auth patterns alone moves you from Mid to Senior-track on security-conscious teams. This is the #1 thing interviewers look for.",
            },
            {
                "gap": "Test-driven development discipline",
                "career_roi": "high",
                "evidence": "react-dashboard has 0 test files across 18 components. cli-toolbox has no tests.",
                "fix": "Start with react-dashboard: add Jest + React Testing Library. Write tests for useAuth hook and Chart component. Target 60% coverage.",
                "promotion_impact": "Senior engineers are expected to write tests as part of their workflow, not as an afterthought. Companies like Stripe and Google auto-reject PRs without tests.",
            },
            {
                "gap": "Code architecture and modularity",
                "career_roi": "medium",
                "evidence": "cli-toolbox/main.go is a 400-line monolith. No package structure, no separation of concerns.",
                "fix": "Refactor cli-toolbox into proper Go packages: cmd/ for CLI entry, internal/parser/ for parsing, internal/formatter/ for output.",
                "promotion_impact": "Demonstrates system design thinking. Senior roles require evidence of building maintainable, team-friendly codebases.",
            },
            {
                "gap": "Error handling consistency",
                "career_roi": "medium",
                "evidence": "ecommerce-api/src/orders/service.py:88-95 bare except clause; cli-toolbox/main.go:120-135 ignored errors.",
                "fix": "Audit all error handling: replace bare except with specific exceptions. Never ignore errors with _. Add structured logging.",
                "promotion_impact": "Sloppy error handling is the most common reason code review PRs get rejected at mature companies.",
            },
            {
                "gap": "Performance optimization awareness",
                "career_roi": "low",
                "evidence": "react-dashboard/src/components/Chart.tsx:22-45 infinite re-render from missing useEffect deps.",
                "fix": "Learn React performance patterns: useMemo, useCallback, dependency arrays. Profile with React DevTools.",
                "promotion_impact": "Performance awareness distinguishes Mid from Senior in frontend roles but is less critical than security and testing.",
            },
        ],
        "roadmap_90_days": [
            {
                "week": "1-2",
                "focus": "Fix critical security vulnerabilities",
                "action": "Replace password comparison with hmac.compare_digest in ecommerce-api. Move JWT from localStorage to httpOnly cookies in react-dashboard. Read OWASP Authentication Cheatsheet.",
                "hours": 8,
            },
            {
                "week": "3-4",
                "focus": "Establish testing foundations",
                "action": "Set up Jest + React Testing Library in react-dashboard. Write 5 unit tests for useAuth hook and 3 integration tests for Chart component. Target 30% coverage.",
                "hours": 10,
            },
            {
                "week": "5-6",
                "focus": "Refactor monolithic Go CLI",
                "action": "Split cli-toolbox/main.go into cmd/, internal/parser/, internal/formatter/ packages. Add Go table-driven tests for parser. Write README with usage examples.",
                "hours": 8,
            },
            {
                "week": "7-8",
                "focus": "Error handling audit",
                "action": "Audit all repos for bare except clauses, ignored errors, and missing error boundaries. Add structured logging with Python logging module and Go log/slog.",
                "hours": 6,
            },
            {
                "week": "9-10",
                "focus": "Test coverage expansion",
                "action": "Reach 60% test coverage in react-dashboard. Add API integration tests for ecommerce-api using pytest + httpx. Set up CI pipeline with GitHub Actions.",
                "hours": 10,
            },
            {
                "week": "11-12",
                "focus": "Portfolio polish and documentation",
                "action": "Write comprehensive READMEs with architecture diagrams for top 2 repos. Add API documentation with OpenAPI/Swagger. Archive or delete cli-toolbox if not refactored.",
                "hours": 6,
            },
        ],
        "resume_bullets": [
            {
                "repo": "ecommerce-api",
                "original_claim": "Built a full-stack e-commerce platform with user authentication",
                "rewritten": "Developed a FastAPI-based e-commerce REST API with JWT authentication, Stripe payment integration, and SQLAlchemy ORM — handles order processing pipeline across 4 service modules (72/100 code quality, auth timing vulnerability identified and fixable).",
            },
            {
                "repo": "react-dashboard",
                "original_claim": "Created an analytics dashboard with React and charts",
                "rewritten": "Built a React + TypeScript analytics dashboard with Recharts data visualization and custom auth hooks — serves as a functional prototype (58/100 quality, needs test coverage and performance optimization before production use).",
            },
            {
                "repo": "cli-toolbox",
                "original_claim": "Developed a CLI tool in Go for file processing",
                "rewritten": "Wrote a Go CLI utility for file parsing and formatting — functional but monolithic single-file architecture (45/100 quality, recommend refactoring into packages before showcasing).",
            },
        ],
        "portfolio_ranking": [
            {
                "repo": "ecommerce-api",
                "rank": 1,
                "action": "lead_with",
                "reason": "Strongest project: clean API design, real payment integration, proper route organization. Fix the auth vulnerability and this becomes a strong portfolio piece.",
            },
            {
                "repo": "react-dashboard",
                "rank": 2,
                "action": "improve",
                "reason": "Good concept but needs tests and performance fixes. Add test coverage and it moves to lead_with tier.",
            },
            {
                "repo": "cli-toolbox",
                "rank": 3,
                "action": "hide",
                "reason": "400-line monolith with ignored errors signals junior habits. Either refactor into proper Go packages or remove from public profile.",
            },
        ],
    },
    "market_intel": {
        "percentile": 62,
        "qualifying_roles": [
            "Mid-Level Backend Developer",
            "Full-Stack Developer",
            "Python Developer",
            "Junior DevOps Engineer",
        ],
        "job_matches": [
            {
                "title": "Mid-Level Python Backend Developer",
                "company": "TechFlow Inc.",
                "url": "https://example.com/jobs/python-backend",
                "match_score": 85,
            },
            {
                "title": "Full-Stack Developer (React + Python)",
                "company": "DataStream Labs",
                "url": "https://example.com/jobs/fullstack",
                "match_score": 78,
            },
            {
                "title": "Software Engineer II",
                "company": "CloudScale Systems",
                "url": "https://example.com/jobs/swe2",
                "match_score": 72,
            },
            {
                "title": "Backend Developer — Go/Python",
                "company": "NetCore Solutions",
                "url": "https://example.com/jobs/backend-go",
                "match_score": 68,
            },
        ],
        "salary_unlock_skills": [
            "Kubernetes",
            "System Design",
            "CI/CD Pipelines",
            "AWS/GCP Cloud",
            "GraphQL",
        ],
    },
}
