#!/usr/bin/env bash
# deploy-flags.sh — runs ON THE HOST. Copies the Stage 4/5 flag artifacts
# (built by scripts/author_flags.py into vm/flag-staging/) onto the VM,
# with correct ownership/permissions. Re-run any time flags are
# regenerated; it overwrites in place.
set -euo pipefail
cd "$(dirname "$0")/.."

KEY="keys/ctfbuilder_ed25519"
PORT=2222
HOST="ctfbuilder@127.0.0.1"
SSH_OPTS=(-i "$KEY" -p "$PORT" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10)
STAGING="flag-staging"

if [ ! -d "$STAGING" ]; then
  echo "Missing $STAGING. Run: app/.venv/bin/python3 ../scripts/author_flags.py" >&2
  exit 1
fi

if ! ssh "${SSH_OPTS[@]}" "$HOST" 'echo ok' >/dev/null 2>&1; then
  echo "Cannot reach the VM over SSH. Is it booted?" >&2
  exit 1
fi

echo "== Copying staged flag artifacts to the VM =="
scp -i "$KEY" -P "$PORT" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -r \
  "$STAGING" "$HOST:/tmp/flag-staging"

echo "== Copying flagcrypto.py (so the admin shell can decrypt on-box) =="
scp -i "$KEY" -P "$PORT" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null \
  ../challenge-data/tools/flagcrypto.py "$HOST:/tmp/flagcrypto.py"
ssh "${SSH_OPTS[@]}" "$HOST" '
sudo mkdir -p /opt/tools
sudo mv /tmp/flagcrypto.py /opt/tools/flagcrypto.py
sudo chmod 755 /opt/tools /opt/tools/flagcrypto.py
'

echo "== Placing them with correct ownership/permissions =="
ssh "${SSH_OPTS[@]}" "$HOST" bash -s <<'REMOTE'
set -euo pipefail
sudo mkdir -p /home/admin/evidence /home/admin/flags /root
sudo cp /tmp/flag-staging/admin-evidence/* /home/admin/evidence/
sudo cp /tmp/flag-staging/admin-flags/* /home/admin/flags/
sudo cp /tmp/flag-staging/root/* /root/
# Glob expansion for paths under directories ctfbuilder itself can't read
# (evidence/flags are mode 750 admin:admin) must happen INSIDE the root
# shell, not in ctfbuilder's shell before sudo runs -- otherwise the `*`
# never expands and chmod gets a literal, nonexistent "...*" path.
sudo bash -c 'chown -R admin:admin /home/admin/evidence /home/admin/flags &&
              chmod 640 /home/admin/evidence/* /home/admin/flags/* &&
              chown -R root:root /root &&
              chmod 600 /root/final_evidence.enc /root/old_evidence.enc /root/root_note.txt'
sudo rm -rf /tmp/flag-staging
echo "Placed."
REMOTE

echo "== Verifying permission boundaries =="
ssh "${SSH_OPTS[@]}" "$HOST" '
echo "-- admin evidence/flags (should be admin:admin, 640) --"
sudo ls -la /home/admin/evidence /home/admin/flags
echo "-- root dir (should be root:root, 600) --"
sudo ls -la /root
echo "-- john cannot read admin evidence --"
sudo -u john cat /home/admin/evidence/decrypt_notes.txt 2>&1 || true
echo "-- admin cannot read root final artifact --"
sudo -u admin cat /root/final_evidence.enc 2>&1 || true
'
echo "Done."
