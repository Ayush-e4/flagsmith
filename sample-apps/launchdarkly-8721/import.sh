#!/usr/bin/env bash
# Run the real Flagsmith LaunchDarkly importer against ld_fixtures/.
# usage: OLD_CHECKOUT=/path/to/flagsmith-main FIXED_CHECKOUT=/path/to/flagsmith-fix ./import.sh old|fixed
# Optional: ENV_FILE=/path/to/api/.env-local to load DATABASE_URL etc.
set -euo pipefail
DEMO_DIR=$(cd "$(dirname "$0")" && pwd)
case "${1:-}" in
  old)   CHECKOUT=${OLD_CHECKOUT:?set OLD_CHECKOUT to a checkout of main} ;;
  fixed) CHECKOUT=${FIXED_CHECKOUT:?set FIXED_CHECKOUT to a checkout of fix/ld-importer-segment-or-8721} ;;
  *) echo "usage: $0 old|fixed" >&2; exit 1 ;;
esac
cd "$CHECKOUT/api"
if [ -n "${ENV_FILE:-}" ]; then set -a; . "$ENV_FILE"; set +a; fi
DEMO_LABEL=$1 DEMO_DIR=$DEMO_DIR uv run --no-sync python manage.py shell -c "exec(open('$DEMO_DIR/run_import.py').read())"
