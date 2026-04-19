import httpx
import time

print("Starting audit for octocat...")
r = httpx.post('http://127.0.0.1:8000/audit', json={'github_username':'octocat'}, timeout=10.0)
print(r.status_code, r.text)
data = r.json()
audit_id = data['audit_id']

print(f"Audit ID: {audit_id}")
print("Polling...")

while True:
    try:
        r_stat = httpx.get(f'http://127.0.0.1:8000/report/{audit_id}/status')
        status_data = r_stat.json()
        print(f"Status: {status_data}")
        if status_data['status'] != 'processing':
            break
    except Exception as e:
        print("Polling error:", e)
    time.sleep(2)

print("Fetching final report...")
r_rep = httpx.get(f'http://127.0.0.1:8000/report/{audit_id}')
if r_rep.status_code == 200:
    print("Success. Total keys:", list(r_rep.json().keys()))
    print("Verdict:", r_rep.json().get('career_verdict', {}).get('verdict'))
else:
    print("Failed to fetch report:", r_rep.status_code, r_rep.text)
