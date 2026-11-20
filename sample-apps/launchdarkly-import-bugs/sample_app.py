"""Sample app: ask a running Flagsmith API which checkout each user gets.

Calls the SDK endpoint POST /api/v1/identities/ (what every Flagsmith SDK calls)
for both imports, in both environments, and compares with Launch Darkly.
Launch Darkly: beta testers get "new", everyone else gets "old". Beta testers
are `tess-tester` in Test and `paula-prod` in Production.
"""
import json, pathlib, urllib.request

API = "http://localhost:8000/api/v1"
HERE = pathlib.Path(__file__).parent
BETA = {"Test": "tess-tester", "Production": "paula-prod"}
USERS = ["tess-tester", "paula-prod", "dave"]

def flagsmith_says(env_key, identifier):
    body = json.dumps({"identifier": identifier,
                       "traits": [{"trait_key": "key", "trait_value": identifier}]}).encode()
    req = urllib.request.Request(f"{API}/identities/", data=body, method="POST",
                                 headers={"X-Environment-Key": env_key, "Content-Type": "application/json"})
    flags = json.load(urllib.request.urlopen(req))["flags"]
    return next(f["feature_state_value"] for f in flags if f["feature"]["name"] == "checkout-version")

imports = {l: json.loads((HERE / f"import_{l}.json").read_text()) for l in ("old", "fixed")}
score = {l: 0 for l in imports}
total = 0
print(f"{'env':11} {'user':12} | {'LaunchDarkly':12} | {'old import':14} | {'fixed import':14}")
print("-" * 72)
for env in ("Test", "Production"):
    for user in USERS:
        expected = "new" if user == BETA[env] else "old"
        got = {l: flagsmith_says(i["environment_keys"][env], user) for l, i in imports.items()}
        total += 1
        cells = []
        for l in ("old", "fixed"):
            ok = got[l] == expected
            score[l] += ok
            cells.append(f"{str(got[l]):6} {'✅' if ok else '❌'}")
        print(f"{env:11} {user:12} | {expected:12} | {cells[0]:13} | {cells[1]:13}")
print("-" * 72)
print(f"matches Launch Darkly: old {score['old']}/{total}, fixed {score['fixed']}/{total}")
print()
for l, i in imports.items():
    print(f"{l} import, segment overrides created:")
    for o in i["segment_overrides"]:
        print(f"  {o['environment']:11} -> {o['linked_segment']:40} {o['percentages']}")
