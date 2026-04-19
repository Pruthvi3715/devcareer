"""One-off: POST /audit for a GitHub username and wait for report."""
import argparse
import json
import sys
import time

import httpx


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("github_username", nargs="?", default="Devendra-006")
    p.add_argument("--base", default="http://127.0.0.1:8000")
    p.add_argument("--timeout", type=int, default=900)
    args = p.parse_args()

    base = args.base.rstrip("/")
    print(f"POST {base}/audit github_username={args.github_username}")
    r = httpx.post(
        f"{base}/audit",
        json={"github_username": args.github_username},
        timeout=60,
    )
    r.raise_for_status()
    aid = r.json()["audit_id"]
    print("audit_id:", aid)

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        s = httpx.get(f"{base}/report/{aid}/status", timeout=30).json()
        st, pr = s.get("status"), s.get("progress", 0)
        line = f"  status={st} progress={pr}%"
        if s.get("message"):
            line += f" | {s['message'][:120]}"
        print(line, flush=True)
        if st == "done":
            break
        if st == "error":
            print("Pipeline error:", json.dumps(s, indent=2))
            return 1
        time.sleep(4)
    else:
        print("Timed out waiting for audit")
        return 2

    rep = httpx.get(f"{base}/report/{aid}", timeout=120)
    print("GET /report status", rep.status_code)
    if rep.status_code != 200:
        print(rep.text[:800])
        return 3

    data = rep.json()
    print("Top-level keys:", sorted(data.keys()))
    cv = data.get("career_verdict") or {}
    print("--- career_verdict.verdict (preview) ---")
    print((cv.get("verdict") or "")[:800])
    print("--- repo_scores count ---", len(data.get("repo_scores") or []))
    print("--- findings count ---", len(data.get("findings") or []))
    return 0


if __name__ == "__main__":
    sys.exit(main())
