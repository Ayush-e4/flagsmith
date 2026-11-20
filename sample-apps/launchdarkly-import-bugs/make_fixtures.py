"""Build a Launch Darkly export that shows two importer bugs.

- The "Beta testers" segment has different members per environment:
  Test includes `tess-tester`, Production includes `paula-prod`.
- The multivariate flag `checkout-version` serves "old" by default and
  "new" to beta testers (a rule with a fixed variation).

Project and environments are copied from Flagsmith's own Launch Darkly test data.
"""
import json, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "api/tests/unit/integrations/launch_darkly/client_responses"
OUT = pathlib.Path(__file__).parent / "ld_fixtures"
OUT.mkdir(exist_ok=True)

project = json.loads((SRC / "get_project.json").read_text())
environments = json.loads((SRC / "get_environments.json").read_text())
env_keys = [e["key"] for e in environments]  # ["test", "production"]

MEMBERS = {"test": ["tess-tester"], "production": ["paula-prod"]}

def segment(env):
    return {
        "name": "Beta testers", "key": "beta-testers", "tags": [],
        "creationDate": 1704302060324, "lastModifiedDate": 1704302081521,
        "included": MEMBERS[env], "excluded": [],
        "includedContexts": [], "excludedContexts": [], "rules": [],
        "version": 1, "deleted": False, "generation": 1, "_links": {},
    }

def env_config():
    return {
        "_environmentName": "x",
        "_summary": {"variations": {"0": {"rules": 1}, "1": {"isFallthrough": True}, "2": {"isOff": True}}},
        "archived": False, "contextTargets": [], "targets": [],
        "fallthrough": {"variation": 1}, "offVariation": 2, "on": True, "prerequisites": [],
        # Rule: users in "Beta testers" get variation 0 ("new").
        "rules": [{"_id": "beta-rule", "description": "Beta testers get new",
                   "clauses": [{"_id": "c1", "attribute": "segmentMatch", "contextKind": "user",
                                "negate": False, "op": "segmentMatch", "values": ["beta-testers"]}],
                   "trackEvents": False, "variation": 0}],
        "salt": "s", "sel": "s", "trackEvents": False, "trackEventsFallthrough": False,
        "version": 1, "lastModified": 1704731410003,
    }

flag = {
    "key": "checkout-version", "name": "checkout-version", "kind": "multivariate",
    "description": "Which checkout a user gets", "archived": False, "deprecated": False,
    "temporary": False, "tags": [], "creationDate": 1704302028410,
    "defaults": {"offVariation": 2, "onVariation": 0},
    "variations": [{"_id": "v0", "name": "New", "value": "new"},
                   {"_id": "v1", "name": "Old", "value": "old"},
                   {"_id": "v2", "name": "Legacy", "value": "legacy"}],
    "environments": {k: env_config() for k in env_keys},
    "_links": {}, "_version": 1, "customProperties": {}, "goalIds": [],
    "experiments": {"baselineIdx": 0, "items": []}, "clientSideAvailability": {},
    "includeInSnippet": False, "maintainerId": "x",
}

files = {"project": project, "environments": environments, "flags": [flag]}
files.update({f"segments_{env}": [segment(env)] for env in env_keys})
for name, data in files.items():
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n")
print("wrote", sorted(files))
