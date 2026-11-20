"""Build LaunchDarkly API-shaped fixtures for the #8721 demo.

Project and environments are copied from Flagsmith's own LD test fixtures.
The flag and segment are hand-written in the exact LD API shape.
"""
import copy, json, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "api/tests/unit/integrations/launch_darkly/client_responses"
OUT = pathlib.Path(__file__).parent / "ld_fixtures"

project = json.loads((SRC / "get_project.json").read_text())
environments = json.loads((SRC / "get_environments.json").read_text())
env_keys = [e["key"] for e in environments]

def clause(attribute, op, values, negate=False):
    return {"_id": f"c-{attribute}", "attribute": attribute, "contextKind": "user",
            "negate": negate, "op": op, "values": values}

# LD segment "beta-testers": a context is IN if it is included, otherwise OUT if
# excluded, otherwise IN if ANY rule matches (rules are OR-ed).
segment = {
    "name": "Beta testers", "key": "beta-testers", "tags": [],
    "creationDate": 1704302060324, "lastModifiedDate": 1704302081521,
    "included": ["vip-user"], "excluded": ["blocked-user"],
    "includedContexts": [], "excludedContexts": [],
    "rules": [
        {"_id": "r1", "clauses": [clause("email", "endsWith", ["@acme.com"])]},
        {"_id": "r2", "clauses": [clause("country", "in", ["NL", "BE"])]},
    ],
    "version": 1, "deleted": False, "generation": 1, "_links": {},
}

def env_config():
    return {
        "_environmentName": "x", "_summary": {"variations": {"0": {"rules": 1}, "1": {"isFallthrough": True}, "2": {"isOff": True}}}, "archived": False, "contextTargets": [], "targets": [],
        "fallthrough": {"variation": 1}, "offVariation": 2, "on": True, "prerequisites": [],
        "rules": [{"_id": "fr1", "clauses": [clause("segmentMatch", "segmentMatch", ["beta-testers"])],
                   "trackEvents": False, "variation": 0}],
        "salt": "s", "sel": "s", "trackEvents": False, "trackEventsFallthrough": False, "version": 1,
        "lastModified": 1704731410003,
    }

flag = {
    "key": "new-checkout", "name": "new-checkout", "kind": "multivariate", "description": "Demo for #8721",
    "archived": False, "deprecated": False, "temporary": False, "tags": [],
    "creationDate": 1704302028410, "defaults": {"offVariation": 2, "onVariation": 0},
    "variations": [{"_id": "v0", "name": "New", "value": "new"}, {"_id": "v1", "name": "Old", "value": "old"}, {"_id": "v2", "name": "Legacy", "value": "legacy"}],
    "environments": {k: env_config() for k in env_keys},
    "_links": {}, "_version": 1, "customProperties": {}, "goalIds": [],
    "experiments": {"baselineIdx": 0, "items": []}, "clientSideAvailability": {},
    "includeInSnippet": False, "maintainerId": "x",
}

for name, data in {"project": project, "environments": environments,
                   "flags": [flag], "segments": [segment]}.items():
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=2))
print("environments:", env_keys)
