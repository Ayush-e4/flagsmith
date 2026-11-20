"""Create demo data for #8261: an org admin (Alice), a project, and an admin
Master API key named "terraform-prod". Run inside `manage.py shell`."""
import json, os, pathlib
from rest_framework.authtoken.models import Token
from api_keys.models import MasterAPIKey
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from users.models import FFAdminUser

user, created = FFAdminUser.objects.get_or_create(
    email="alice@audit-demo.example", defaults={"first_name": "Alice", "last_name": "Admin"})
user.set_password("demo-password-8261"); user.save()
org, _ = Organisation.objects.get_or_create(name="Audit log demo (#8261)")
if not user.belongs_to(org.id):
    user.add_organisation(org, OrganisationRole.ADMIN)
# Audit logs are hidden on the free plan, so put the demo org on enterprise.
org.subscription.plan = "enterprise"; org.subscription.save()
project, _ = Project.objects.get_or_create(organisation=org, name="audit-demo")
env, _ = Environment.objects.get_or_create(project=project, name="Production")
MasterAPIKey.objects.filter(organisation=org, name="terraform-prod").delete()
_, key = MasterAPIKey.objects.create_key(name="terraform-prod", organisation=org, is_admin=True)
token, _ = Token.objects.get_or_create(user=user)
out = {"org_id": org.id, "project_id": project.id, "user_token": token.key,
       "master_api_key": key, "login": [user.email, "demo-password-8261"]}
pathlib.Path(os.environ["DEMO_DIR"], "setup.json").write_text(json.dumps(out, indent=2))
print("ok", {k: v for k, v in out.items() if k in ("org_id", "project_id")})
