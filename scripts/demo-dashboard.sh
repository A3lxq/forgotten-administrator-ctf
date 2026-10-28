#!/usr/bin/env bash
# demo-dashboard.sh — populates a running dashboard with realistic fake
# team activity, so you can see the leaderboard and score-over-time
# chart actually working without powering up the CTF VM at all. The
# dashboard must already be running (./scripts/run-dashboard.sh in
# another terminal) -- this script only talks to it over HTTP, the
# same way a real player's browser would.
#
# Set DASHBOARD_URL to point at a non-default host/port; otherwise
# assumes http://127.0.0.1:7000.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/demo_dashboard_seed.py
