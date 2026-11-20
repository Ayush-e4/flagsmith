"""Run the real Flagsmith Launch Darkly importer against ld_fixtures/.

Executed inside `manage.py shell` of a Flagsmith checkout, so the importer under
test is whichever checkout runs it (old = main, fixed = the fix branch). Only
Launch Darkly's HTTP API is replaced by a stub that returns ld_fixtures/.
Writes import_<label>.json with what the importer created.
"""
import json, os, pathlib
from unittest import mock

from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.launch_darkly import services
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from users.models import FFAdminUser

LABEL = os.environ["DEMO_LABEL"]
HERE = pathlib.Path(os.environ["DEMO_DIR"])
load = lambda n: json.loads((HERE / "ld_fixtures" / f"{n}.json").read_text())


class StubLaunchDarklyClient:
    def __init__(self, token): pass
    def get_project(self, project_key): return load("project")
    def get_environments(self, project_key): return load("environments")
    def get_flags_by_envs(self, project_key, environment_keys): return load("flags")
    def get_flag_count(self, project_key): return 1
    def get_flag_tags(self): return []
    def get_segment_tags(self): return []
    def get_segments(self, project_key, environment_key):
        return load(f"segments_{environment_key}")


user, _ = FFAdminUser.objects.get_or_create(
    email="ld-import-demo@example.com", defaults={"first_name": "LD", "last_name": "Demo"})
org, _ = Organisation.objects.get_or_create(name="LD import bugs demo")
if not user.belongs_to(org.id):
    user.add_organisation(org, OrganisationRole.ADMIN)
Project.objects.filter(organisation=org, name=f"ld-import-bugs-{LABEL}").delete()
project = Project.objects.create(organisation=org, name=f"ld-import-bugs-{LABEL}")

with mock.patch.object(services, "LaunchDarklyClient", StubLaunchDarklyClient):
    request = services.create_import_request(
        project=project, user=user, ld_project_key="demo", ld_token="x")
    services.process_import_request(request)
request.refresh_from_db()

feature = Feature.objects.get(project=project, name="checkout-version")
overrides = [
    {
        "environment": fs.environment.name,
        "linked_segment": fs.feature_segment.segment.name,
        "percentages": {
            v.multivariate_feature_option.string_value: v.percentage_allocation
            for v in fs.multivariate_feature_state_values.all()
        },
    }
    for fs in FeatureState.objects.filter(
        feature=feature, feature_segment__isnull=False, identity__isnull=True
    ).order_by("environment__name")
]
out = {
    "label": LABEL,
    "import_result": request.status.get("result"),
    "segment_overrides": overrides,
    "environment_keys": {e.name: e.api_key for e in Environment.objects.filter(project=project)},
}
(HERE / f"import_{LABEL}.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
print(json.dumps(out, indent=2, default=str))
