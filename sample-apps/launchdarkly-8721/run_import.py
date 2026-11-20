"""Run a real Flagsmith LaunchDarkly import against the demo fixtures.

Executed inside `manage.py shell` of a Flagsmith checkout, so the import code
under test is whichever checkout runs it (old = main, fixed = #8721 branch).
Only LaunchDarkly's HTTP API is replaced: the stub returns the JSON in
ld_fixtures/, exactly what LaunchDarklyClient would have parsed.
"""
import json, os, pathlib
from unittest import mock

from environments.models import Environment
from integrations.launch_darkly import services
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser

LABEL = os.environ["DEMO_LABEL"]
FIX = pathlib.Path(os.environ["DEMO_DIR"]) / "ld_fixtures"
load = lambda n: json.loads((FIX / f"{n}.json").read_text())


class StubLaunchDarklyClient:
    def __init__(self, token): pass
    def get_project(self, project_key): return load("project")
    def get_environments(self, project_key): return load("environments")
    def get_flags_by_envs(self, project_key, environment_keys): return load("flags")
    def get_flag_count(self, project_key): return 1
    def get_flag_tags(self): return []
    def get_segment_tags(self): return []
    def get_segments(self, project_key, environment_key): return load("segments")


user, _ = FFAdminUser.objects.get_or_create(
    email="ld-demo@example.com", defaults={"first_name": "LD", "last_name": "Demo"})
org, _ = Organisation.objects.get_or_create(name="LD import demo (#8721)")
if not user.belongs_to(org.id):
    user.add_organisation(org, OrganisationRole.ADMIN)
Project.objects.filter(organisation=org, name=f"ld-import-{LABEL}").delete()
project = Project.objects.create(organisation=org, name=f"ld-import-{LABEL}")

with mock.patch.object(services, "LaunchDarklyClient", StubLaunchDarklyClient):
    req = services.create_import_request(project=project, user=user, ld_project_key="demo", ld_token="x")
    services.process_import_request(req)
req.refresh_from_db()

print("STATUS", req.status); print("SEGMENTS", list(Segment.objects.filter(project=project).values_list("name", flat=True)))
seg = Segment.objects.filter(project=project, name="Beta testers (Override for test)").get()
# Use the imported segment the way a user would: a feature that is OFF by
# default and ON for the imported "Beta testers" segment in the Test env.
from features.models import Feature, FeatureSegment, FeatureState
test_env = Environment.objects.get(project=project, name="Test")
feature = Feature.objects.create(project=project, name="beta-checkout", default_enabled=False)
fseg = FeatureSegment.objects.create(feature=feature, segment=seg, environment=test_env)
FeatureState.objects.create(feature=feature, environment=test_env, feature_segment=fseg, enabled=True)

out = {
    "label": LABEL,
    "project_id": project.id,
    "import_status": req.status,
    "segment_rules_data": seg.rules_data if hasattr(seg, "rules_data") else None,
    "environments": {e.name: e.api_key for e in Environment.objects.filter(project=project)},
}
pathlib.Path(os.environ["DEMO_DIR"], f"import_{LABEL}.json").write_text(json.dumps(out, indent=2, default=str))
print(json.dumps(out, indent=2, default=str))
