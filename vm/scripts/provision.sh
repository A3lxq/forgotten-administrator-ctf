#!/usr/bin/env bash
# provision.sh — runs ON THE HOST. Copies the app source and
# remote-provision.sh into the running VM over SSH (as ctfbuilder) and
# executes the remote script there. Re-run any time the app changes.
set -euo pipefail
cd "$(dirname "$0")/.."

KEY="keys/ctfbuilder_ed25519"
PORT=2222
HOST="ctfbuilder@127.0.0.1"
SSH_OPTS=(-i "$KEY" -p "$PORT" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10)

if ! ssh "${SSH_OPTS[@]}" "$HOST" 'echo ok' >/dev/null 2>&1; then
  echo "Cannot reach the VM over SSH (127.0.0.1:2222). Is it booted? (./scripts/boot-vm.sh)" >&2
  exit 1
fi

echo "== Copying app source to the VM =="
rsync -az --delete -e "ssh ${SSH_OPTS[*]}" \
  --exclude ".venv" --exclude "__pycache__" --exclude "instance" --exclude ".pytest_cache" \
  ../app/ "$HOST:/tmp/forgotten-admin-app/"

echo "== Copying player materials (Stage 1-3 content) to the VM =="
# Only the player-safe subset of challenge-data/ -- never instructor-material.
# stage3-git-history.tar.gz may not exist yet if author_flags.py hasn't run.
if [ ! -f ../challenge-data/stage3-git-history.tar.gz ]; then
  echo "Missing ../challenge-data/stage3-git-history.tar.gz. Run:" >&2
  echo "  app/.venv/bin/python3 scripts/author_flags.py" >&2
  exit 1
fi
rsync -az --delete -e "ssh ${SSH_OPTS[*]}" \
  --exclude "stage3-git-history/" \
  ../challenge-data/ "$HOST:/tmp/forgotten-admin-public-data/"

echo "== Copying and running remote-provision.sh =="
scp -i "$KEY" -P "$PORT" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null \
  scripts/remote-provision.sh "$HOST:/tmp/remote-provision.sh"
ssh "${SSH_OPTS[@]}" "$HOST" 'chmod +x /tmp/remote-provision.sh && /tmp/remote-provision.sh'

echo "Provisioning complete."
