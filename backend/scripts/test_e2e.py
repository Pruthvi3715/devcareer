"""
End-to-end test: poll /report/{id}/status until done, then fetch and validate /report/{id}.
Usage: python scripts/test_e2e.py [github_username] [audit_id]
"""
import sys
import requests
import time
import json

BASE = "http://localhost:8000"
USERNAME = sys.argv[1] if len(sys.argv) > 1 else "gvanrossum"
AUDIT_ID = sys.argv[2] if len(sys.argv) > 2 else None

if not AUDIT_ID:
    print(f"Triggering audit for: {USERNAME}")
    r = requests.post(f"{BASE}/audit", json={"github_username": USERNAME}, timeout=15)
    print(f"POST /audit -> {r.status_code}")
    data = r.json()
    AUDIT_ID = data.get("audit_id")
    print(f"audit_id: {AUDIT_ID}")
    print(f"Response: {data}")

print(f"\nPolling /report/{AUDIT_ID}/status ...")
for i in range(80):
    r = requests.get(f"{BASE}/report/{AUDIT_ID}/status", timeout=10)
    s = r.json()
    print(f"  [{i*5}s] status={s.get('status')}  progress={s.get('progress')}")
    if s.get("status") in ("done", "error"):
        print(f"\nFinal status: {json.dumps(s, indent=2)}")
        break
    time.sleep(5)

if s.get("status") == "done":
    print("\nFetching /report/{id} ...")
    r = requests.get(f"{BASE}/report/{AUDIT_ID}", timeout=15)
    report = r.json()

    # Validate top-level schema (PRD §6.2)
    required_fields = ["audit_id", "github_username", "generated_at",
                       "activity_snapshot", "repo_scores", "career_verdict", "market_intel"]
    missing = [f for f in required_fields if f not in report]

    if missing:
        print(f"SCHEMA FAIL — missing fields: {missing}")
    else:
        print("SCHEMA OK — all required fields present")
        print(f"  github_username: {report['github_username']}")
        print(f"  generated_at: {report['generated_at']}")
        act = report["activity_snapshot"]
        print(f"  activity: repos={act.get('repo_count')} langs={act.get('top_languages')} years={act.get('years_active')}")
        print(f"  repo_scores count: {len(report['repo_scores'])}")
        cv = report["career_verdict"]
        print(f"  career_verdict.verdict: {cv.get('verdict')}")
        print(f"  career_verdict.confidence: {cv.get('confidence')}")
        print(f"  gap_analysis items: {len(cv.get('gap_analysis', []))}")
        print(f"  roadmap items: {len(cv.get('roadmap_90_days', []))}")
        mi = report["market_intel"]
        print(f"  market_intel.percentile: {mi.get('percentile')}")
        print(f"  job_matches count: {len(mi.get('job_matches', []))}")
        print(f"  qualifying_roles: {mi.get('qualifying_roles')}")
else:
    print("Pipeline did not complete — check server logs")
