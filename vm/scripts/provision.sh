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

echo "== Copying and running remote-provision.sh =="
scp -i "$KEY" -P "$PORT" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null \
  scripts/remote-provision.sh "$HOST:/tmp/remote-provision.sh"
ssh "${SSH_OPTS[@]}" "$HOST" 'chmod +x /tmp/remote-provision.sh && /tmp/remote-provision.sh'

echo "Provisioning complete."
