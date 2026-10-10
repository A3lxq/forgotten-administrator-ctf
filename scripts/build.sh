#!/usr/bin/env bash
# build.sh — full build from a clean checkout: VM, app, flags, privesc
# weakness, all deployed and verified reachable. Delegates to the real
# logic under vm/scripts/ rather than duplicating it.
#
# Assumes: vm/images/ubuntu-24.04-server-cloudimg-amd64.img already
# downloaded and checksum-verified (see instructor-material/build-guide.md
# — this is a one-time, internet-requiring step this script does not do
# for you, per Section 20's "explain any temporary internet access
# needed" rather than silently fetching things).
# Assumes: vm/keys/ctfbuilder_ed25519 already generated and its .pub
# pasted into vm/cloud-init/user-data.yaml (also one-time, see the same
# guide) — build.sh does not generate keys or edit cloud-init config.
set -euo pipefail
cd "$(dirname "$0")/.."

BASE_IMAGE="vm/images/ubuntu-24.04-server-cloudimg-amd64.img"
KEY="vm/keys/ctfbuilder_ed25519"

if [ ! -f "$BASE_IMAGE" ]; then
  echo "Missing $BASE_IMAGE." >&2
  echo "See instructor-material/build-guide.md's 'One-time: download and verify the base image' step." >&2
  exit 1
fi
if [ ! -f "$KEY" ]; then
  echo "Missing $KEY." >&2
  echo "See instructor-material/build-guide.md's 'Build the instructor SSH key' step." >&2
  exit 1
fi

echo "== [1/6] App venv + tests =="
if [ ! -x app/.venv/bin/pytest ]; then
  python3 -m venv app/.venv
  app/.venv/bin/pip install -q -r app/requirements.txt
fi
./scripts/run-tests.sh

echo "== [2/6] Creating VM disk =="
(cd vm && ./scripts/create-disk.sh --force)

echo "== [3/6] Booting VM and waiting for cloud-init =="
(cd vm && ./scripts/boot-vm.sh)
SSH="ssh -i vm/keys/ctfbuilder_ed25519 -p 2222 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"
tries=0
until $SSH ctfbuilder@127.0.0.1 'cloud-init status 2>/dev/null' 2>/dev/null | grep -qE 'status: (done|error)'; do
  tries=$((tries+1))
  if [ "$tries" -gt 90 ]; then
    echo "Timed out waiting for cloud-init (90 * 10s). Check vm/logs for details." >&2
    exit 1
  fi
  sleep 10
done
echo "cloud-init finished."

echo "== [4/6] Provisioning the app + privesc weakness =="
(cd vm && ./scripts/provision.sh)

echo "== [5/6] Building and deploying flags =="
app/.venv/bin/python3 scripts/author_flags.py
./scripts/validate-flags.sh
(cd vm && ./scripts/deploy-flags.sh)

echo "== [6/6] Health check =="
./scripts/health-check.sh

echo
echo "Build complete. Consider taking a clean snapshot now:"
echo "  cd vm && ./scripts/stop-vm.sh && qemu-img snapshot -c clean-start disks/forgotten-admin.qcow2 && ./scripts/boot-vm.sh"
