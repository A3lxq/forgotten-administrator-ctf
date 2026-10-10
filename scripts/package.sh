#!/usr/bin/env bash
# package.sh — assembles two SEPARATE deliverables:
#   dist/player-package/     -- safe to hand to participants
#   dist/instructor-package/ -- private; never hand this to participants
#
# Does not build or export the VM itself (see vm/scripts/export-vm.sh
# for that) -- this script packages docs/source/data and, if an export
# already exists under vm/dist/, includes it in the instructor package.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="dist"
PLAYER="$OUT/player-package"
INSTRUCTOR="$OUT/instructor-package"

rm -rf "$PLAYER" "$INSTRUCTOR"
mkdir -p "$PLAYER" "$INSTRUCTOR"

echo "== Player package =="
cp -r player-material "$PLAYER/"
mkdir -p "$PLAYER/challenge-data"
for d in stage1-osint stage2-metadata tools; do
  if [ -d "challenge-data/$d" ]; then
    rsync -a --exclude "__pycache__" --exclude "*.pyc" \
      "challenge-data/$d/" "$PLAYER/challenge-data/$d/"
  fi
done
if [ ! -d "challenge-data/stage3-git-history" ]; then
  echo "challenge-data/stage3-git-history is missing (it's gitignored and" >&2
  echo "regenerated). Run: app/.venv/bin/python3 scripts/author_flags.py" >&2
  exit 1
fi
cp -r challenge-data/stage3-git-history "$PLAYER/challenge-data/"

echo "== Instructor package =="
cp -r instructor-material "$INSTRUCTOR/"
mkdir -p "$INSTRUCTOR/app"
rsync -a --exclude ".venv" --exclude "__pycache__" --exclude "instance" --exclude ".pytest_cache" \
  app/ "$INSTRUCTOR/app/"
cp -r scripts "$INSTRUCTOR/"
mkdir -p "$INSTRUCTOR/vm"
rsync -a --exclude "images" --exclude "disks" --exclude "seed" --exclude "flag-staging" --exclude "dist" \
  vm/ "$INSTRUCTOR/vm/"
if [ -d vm/keys ]; then
  cp -r vm/keys "$INSTRUCTOR/vm/keys"
fi
if [ -d vm/dist ]; then
  cp -r vm/dist "$INSTRUCTOR/vm/dist"
fi
cp README.md PROJECT-STATUS.md CHANGELOG.md DEPENDENCIES.md "$INSTRUCTOR/"

echo "== Safety check: no decrypted genuine-flag values leak into the player package =="
# Flags 1/2 are INTENTIONALLY plaintext in challenge-data (that's the
# puzzle). Flags 3/4/5 only exist as plaintext after a player decrypts
# them -- their decrypted values must never appear in any shipped file.
leak=0
for value in \
  "SYN{git_ghost_61ace7b2}" \
  "SYN{admin_blindspot_9f4e2c18}" \
  "SYN{root_of_all_evidence_3b7d55a0}"
do
  if grep -r -l --binary-files=without-match -- "$value" "$PLAYER" 2>/dev/null; then
    echo "LEAK: decrypted flag value '$value' found in the player package!" >&2
    leak=1
  fi
done
if [ "$leak" -ne 0 ]; then
  echo "Aborting -- do not distribute dist/player-package as-is." >&2
  exit 1
fi
echo "No leaks found."

echo "== Safety check: instructor manifest is not inside the player package =="
if [ -e "$PLAYER/flag-manifest.json" ] || find "$PLAYER" -iname 'flag-manifest.json' | grep -q .; then
  echo "LEAK: flag-manifest.json found inside the player package!" >&2
  exit 1
fi
echo "Confirmed absent."

echo
echo "Done."
du -sh "$PLAYER" "$INSTRUCTOR"
