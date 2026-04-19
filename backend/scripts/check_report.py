import requests, json

aid = "7bad1ffc-d63f-470e-b70f-361b381e3ee6"
r = requests.get(f"http://localhost:8000/report/{aid}")
d = r.json()

print("Status:", r.status_code)
print("Username:", d.get("github_username"))

v = d.get("career_verdict", {})
print("\n=== CAREER VERDICT ===")
print("Verdict:", v.get("verdict"), "| Confidence:", v.get("confidence"))
print("Evidence count:", len(v.get("verdict_evidence", [])))
print("Gap analysis items:", len(v.get("gap_analysis", [])))
print("Roadmap steps:", len(v.get("roadmap_90_days", [])))
print("Resume bullets:", len(v.get("resume_bullets", [])))
print("Portfolio ranked:", len(v.get("portfolio_ranking", [])))

print("\n=== REPOS ===")
for repo in d.get("repo_scores", []):
    name = repo["repo_name"]
    score = repo["score"]
    findings = len(repo.get("findings", []))
    summaries = len(repo.get("module_summaries", {}))
    onboard = len(repo.get("onboarding_path", []))
    print(f"  {name}: score={score}, findings={findings}, module_summaries={summaries}, onboarding_steps={onboard}")

m = d.get("market_intel", {})
print("\n=== MARKET INTEL ===")
print("Percentile:", m.get("percentile"))
print("Qualifying roles:", m.get("qualifying_roles"))
print("Job matches:", len(m.get("job_matches", [])))
print("Salary unlock skills:", m.get("salary_unlock_skills"))

# Show first verdict evidence
if v.get("verdict_evidence"):
    print("\n=== SAMPLE EVIDENCE ===")
    for e in v["verdict_evidence"][:3]:
        print(f"  - {e[:120]}")
