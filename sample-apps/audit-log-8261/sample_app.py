"""Sample app for #8261: make one change with a Master API key (like Terraform
or CI would) and one as a human, then read the organisation audit log from
both API builds: old (port 8001, main) and fixed (port 8000, #8261 branch)."""
import json, pathlib, time, urllib.request

cfg = json.loads((pathlib.Path(__file__).parent / "setup.json").read_text())
suffix = time.strftime("%H%M%S")

def call(base, method, path, auth, body=None):
    req = urllib.request.Request(f"{base}/api/v1{path}", method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": auth, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))

KEY = f"Api-Key {cfg['master_api_key']}"
USER = f"Token {cfg['user_token']}"
FIXED, OLD = "http://localhost:8000", "http://localhost:8001"

# 1. Changes: one by the API key, one by Alice (both via the fixed server).
call(FIXED, "POST", f"/projects/{cfg['project_id']}/features/", KEY, {"name": f"terraform_flag_{suffix}"})
call(FIXED, "POST", f"/projects/{cfg['project_id']}/features/", USER, {"name": f"alice_flag_{suffix}"})
time.sleep(1)

def old_ui(e):  # main: AuditLog.tsx renders `{author?.first_name} {author?.last_name}`
    a = e.get("author") or {}
    return f"{a.get('first_name','')} {a.get('last_name','')}".strip() or "(blank)"

def shown_as(e):  # #8261: mirrors frontend getAuditLogAuthor()
    if e.get("author"): return f"{e['author'].get('first_name','')} {e['author'].get('last_name','')}".strip()
    if e.get("master_api_key"): return f"{e['master_api_key']['name']} (API key)"
    if e.get("is_system_event"): return "System"
    return "Unknown"

for label, base, ui in (("OLD  (main API :8001 + main UI)", OLD, old_ui), ("FIXED (#8261 API :8000 + #8261 UI)", FIXED, shown_as)):
    logs = call(base, "GET", f"/organisations/{cfg['org_id']}/audit/?page_size=50", USER)["results"]
    logs = [e for e in logs if suffix in e["log"]]
    print(f"\n=== {label} ===")
    for e in logs:
        print(f"- {e['log'].split(': ')[-1]:24} | author={'yes' if e.get('author') else 'null':4} "
              f"| master_api_key={json.dumps(e.get('master_api_key', '<field absent>'))} | UI shows: {ui(e)}")
