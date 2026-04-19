import requests, time

aid = "bdcc2de8-acfc-4571-8c1c-381d7dfe512d"
for i in range(12):
    r = requests.get(f"http://localhost:8000/report/{aid}/status")
    s = r.json()
    print(f"{i*5}s: {s}")
    if s.get("status") in ("done", "error"):
        break
    time.sleep(5)

# Fetch full report
r = requests.get(f"http://localhost:8000/report/{aid}")
d = r.json()
v = d.get("career_verdict", {})
print("\n=== VERDICT ===")
print("Verdict:", v.get("verdict"), "| Confidence:", v.get("confidence"))
print("Evidence:", v.get("verdict_evidence", [])[:2])
print("Gaps:", len(v.get("gap_analysis", [])))
print("Roadmap:", len(v.get("roadmap_90_days", [])))
print("Bullets:", len(v.get("resume_bullets", [])))
for repo in d.get("repo_scores", []):
    print(f"  {repo['repo_name']}: score={repo['score']}, findings={len(repo.get('findings',[]))}, summaries={len(repo.get('module_summaries',{}))}")
