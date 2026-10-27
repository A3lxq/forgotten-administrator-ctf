#!/usr/bin/env bash
# run-dashboard.sh — starts the scoring dashboard for a live event.
# Runs on THIS machine (the instructor's host), not the CTF VM -- see
# instructor-material/dashboard-guide.md for the full event-day flow.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x dashboard/.venv/bin/python3 ]; then
    echo "dashboard/.venv doesn't exist yet. Run:" >&2
    echo "  python3 -m venv dashboard/.venv" >&2
    echo "  dashboard/.venv/bin/pip install -r dashboard/requirements.txt" >&2
    exit 2
fi

if [ -z "${DASHBOARD_ADMIN_PASSCODE:-}" ]; then
    echo "DASHBOARD_ADMIN_PASSCODE is not set -- /admin (End Event, reset," >&2
    echo "remove a team) will be unreachable. Set it before a real event:" >&2
    echo "  export DASHBOARD_ADMIN_PASSCODE='pick-something-only-you-know'" >&2
    echo "Continuing anyway -- the public leaderboard/submission pages still work." >&2
fi

port="${DASHBOARD_PORT:-7000}"
echo "Starting the dashboard on 0.0.0.0:${port} ..."
echo "Players on the same LAN reach it at http://<this-machine's-IP>:${port}/"
cd dashboard && exec .venv/bin/python3 wsgi.py
