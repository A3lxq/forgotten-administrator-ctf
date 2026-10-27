#!/usr/bin/env bash
# run-dashboard-tests.sh — runs the scoring dashboard's automated test
# suite. Requires dashboard/.venv to exist (python3 -m venv dashboard/.venv
# && dashboard/.venv/bin/pip install -r dashboard/requirements.txt). Does
# not create it itself, so a missing venv fails loudly instead of
# silently testing nothing.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x dashboard/.venv/bin/pytest ]; then
    echo "dashboard/.venv has no pytest. Run:" >&2
    echo "  python3 -m venv dashboard/.venv" >&2
    echo "  dashboard/.venv/bin/pip install -r dashboard/requirements.txt" >&2
    exit 2
fi

cd dashboard && .venv/bin/pytest tests -v
