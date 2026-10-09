#!/usr/bin/env bash
# run-tests.sh — runs the application's automated test suite.
# Requires app/.venv to exist (python3 -m venv app/.venv && app/.venv/bin/pip
# install -r app/requirements.txt). Does not create it itself, so a missing
# venv fails loudly instead of silently testing nothing.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x app/.venv/bin/pytest ]; then
    echo "app/.venv has no pytest. Run:" >&2
    echo "  python3 -m venv app/.venv" >&2
    echo "  app/.venv/bin/pip install -r app/requirements.txt" >&2
    exit 2
fi

app/.venv/bin/pytest app/tests -v
