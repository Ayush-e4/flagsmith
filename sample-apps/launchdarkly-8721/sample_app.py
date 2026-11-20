"""Sample app: ask the running Flagsmith API which users get `beta-checkout` (ON only for the imported segment).

Uses the public SDK endpoint POST /api/v1/identities/ (what every Flagsmith SDK
calls) with each imported project's environment key, and compares the answer
with LaunchDarkly's documented segment semantics.
"""
import json, pathlib, urllib.request

API = "http://localhost:8000/api/v1"
HERE = pathlib.Path(__file__).parent

USERS = [  # (identifier, traits)
    ("alice",        {"email": "alice@acme.com", "country": "US"}),  # rule 1 only
    ("bob",          {"email": "bob@gmail.com",  "country": "NL"}),  # rule 2 only
    ("carol",        {"email": "carol@acme.com", "country": "BE"}),  # both rules
    ("dave",         {"email": "dave@gmail.com", "country": "US"}),  # no rule
    ("vip-user",     {"email": "vip@gmail.com",  "country": "US"}),  # included list
    ("blocked-user", {"email": "x@acme.com",     "country": "NL"}),  # excluded list
]

def launchdarkly_expected(identifier, t):
    if identifier == "vip-user":      return True    # included wins
    if identifier == "blocked-user":  return False   # then excluded
    return t["email"].endswith("@acme.com") or t["country"] in ("NL", "BE")  # rules OR-ed

def flagsmith_says(env_key, identifier, traits):
    traits = {**traits, "key": identifier}  # LD context key, as the importer expects
    body = json.dumps({"identifier": f"{identifier}", "traits": [
        {"trait_key": k, "trait_value": v} for k, v in traits.items()]}).encode()
    req = urllib.request.Request(f"{API}/identities/", data=body, method="POST",
        headers={"X-Environment-Key": env_key, "Content-Type": "application/json"})
    flags = json.load(urllib.request.urlopen(req))["flags"]
    return next(f["enabled"] for f in flags if f["feature"]["name"] == "beta-checkout")

rows, ok = [], {"old": 0, "fixed": 0}
keys = {l: json.loads((HERE / f"import_{l}.json").read_text())["environments"]["Test"] for l in ok}
for ident, traits in USERS:
    exp = launchdarkly_expected(ident, traits)
    got = {l: flagsmith_says(keys[l], ident, traits) for l in ok}
    for l in ok: ok[l] += got[l] == exp
    rows.append((ident, traits["email"], traits["country"], exp, got["old"], got["fixed"]))

mark = lambda v, e: f"{'ON ' if v else 'off'} {'✅' if v == e else '❌'}"
print(f"{'user':13} {'email':16} {'ctry':4} | {'LaunchDarkly':12} | {'old import':10} | {'fixed import':12}")
print("-" * 80)
for i, e, c, exp, old, fixed in rows:
    print(f"{i:13} {e:16} {c:4} | {'ON' if exp else 'off':12} | {mark(old, exp):10} | {mark(fixed, exp):12}")
print("-" * 80)
print(f"matches LaunchDarkly: old {ok['old']}/{len(USERS)}, fixed {ok['fixed']}/{len(USERS)}")
