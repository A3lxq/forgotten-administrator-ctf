#!/usr/bin/env bash
# reset-dashboard.sh — wipes all teams/submissions/event state for a
# fresh dashboard run (a new team, a new class, a re-run of the event).
# Does not touch the CTF VM or instructor-material/flag-manifest.json --
# only this dashboard's own SQLite database.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x dashboard/.venv/bin/flask ]; then
    echo "dashboard/.venv doesn't exist yet. Run:" >&2
    echo "  python3 -m venv dashboard/.venv" >&2
    echo "  dashboard/.venv/bin/pip install -r dashboard/requirements.txt" >&2
    exit 2
fi

cd dashboard && FLASK_APP="app:create_app" .venv/bin/flask reset-db
