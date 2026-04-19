import requests, time

# Trigger audit
r = requests.post("http://localhost:8000/audit", json={"github_username": "karpathy"})
print("Trigger:", r.status_code, r.json())
aid = r.json()["audit_id"]

# Poll until done
for i in range(24):
    time.sleep(5)
    s = requests.get(f"http://localhost:8000/report/{aid}/status").json()
    print(f"{(i+1)*5}s: {s}")
    if s.get("status") in ("done", "error"):
        break

# Full report
r = requests.get(f"http://localhost:8000/report/{aid}")
d = r.json()
v = d.get("career_verdict", {})
print("\n=== CAREER VERDICT ===")
print("Verdict:", v.get("verdict"), "| Confidence:", v.get("confidence"))
print("Evidence:", len(v.get("verdict_evidence", [])))
print("Gaps:", len(v.get("gap_analysis", [])))
print("Roadmap:", len(v.get("roadmap_90_days", [])))
print("Resume bullets:", len(v.get("resume_bullets", [])))
print("Portfolio:", len(v.get("portfolio_ranking", [])))
print("\n=== REPOS ===")
for repo in d.get("repo_scores", []):
    print(f"  {repo['repo_name']}: score={repo['score']}, findings={len(repo.get('findings',[]))}, summaries={len(repo.get('module_summaries',{}))}, onboard={len(repo.get('onboarding_path',[]))}")
m = d.get("market_intel", {})
print("\n=== MARKET ===")
print("Percentile:", m.get("percentile"))
print("Roles:", m.get("qualifying_roles"))
if v.get("verdict_evidence"):
    print("\n=== SAMPLE EVIDENCE ===")
    for e in v["verdict_evidence"][:3]:
        print(f"  - {str(e)[:150]}")
