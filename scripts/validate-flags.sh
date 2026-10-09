#!/usr/bin/env bash
# validate-flags.sh — instructor-only. Runs the real flag validation
# utility (Section 18): counts, encryption distribution, uniqueness,
# format, scoring, and actual decrypt/reject-wrong-password checks.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x app/.venv/bin/python3 ]; then
  echo "app/.venv is missing. See DEPENDENCIES.md." >&2
  exit 2
fi

app/.venv/bin/python3 scripts/validate_flags.py
