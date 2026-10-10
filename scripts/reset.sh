#!/usr/bin/env bash
# reset.sh — reset between teams/runs. Three modes (see also
# instructor-material/reset-guide.md for the full explanation of each):
#
#   ./scripts/reset.sh app       - wipe + re-seed the web app's DB only
#   ./scripts/reset.sh privesc   - restore the Stage 5 weakness + clear
#                                  known exploit artifacts
#   ./scripts/reset.sh vm        - full VM rollback to the clean-start
#                                  snapshot (requires that snapshot to
#                                  exist -- see build.sh's final step)
#
# Never touches anything outside vm/disks, vm/seed, or the VM's own
# filesystem. Never touches the host machine.
set -euo pipefail
cd "$(dirname "$0")/.."

mode="${1:-}"
case "$mode" in
  app)
    ssh -i vm/keys/ctfbuilder_ed25519 -p 2222 -o StrictHostKeyChecking=accept-new \
        -o UserKnownHostsFile=/dev/null ctfbuilder@127.0.0.1 \
        'sudo systemctl stop forgotten-admin && sudo rm -f /opt/forgotten-admin/app/instance/*.sqlite3'
    (cd vm && ./scripts/provision.sh)
    ;;
  privesc)
    (cd vm && ./scripts/reset-privesc.sh)
    ;;
  vm)
    # qemu-img needs the disk's write lock, which the running VM holds --
    # stop it first, THEN check/apply the snapshot.
    (cd vm && ./scripts/stop-vm.sh)
    if ! (cd vm && qemu-img snapshot -l disks/forgotten-admin.qcow2 2>/dev/null | grep -q clean-start); then
      echo "No 'clean-start' snapshot exists yet. Build one first (VM is now stopped):" >&2
      echo "  cd vm && qemu-img snapshot -c clean-start disks/forgotten-admin.qcow2 && ./scripts/boot-vm.sh" >&2
      exit 1
    fi
    (cd vm && qemu-img snapshot -a clean-start disks/forgotten-admin.qcow2)
    (cd vm && ./scripts/boot-vm.sh)
    echo "Restored to the clean-start snapshot. Waiting for the app to come back up..."
    tries=0
    until curl -sf http://127.0.0.1:8080/healthz >/dev/null 2>&1; do
      tries=$((tries+1))
      [ "$tries" -gt 30 ] && { echo "App did not come back up within 150s." >&2; exit 1; }
      sleep 5
    done
    echo "App is back up."
    ;;
  *)
    echo "Usage: $0 {app|privesc|vm}" >&2
    echo "See instructor-material/reset-guide.md for what each does." >&2
    exit 2
    ;;
esac

echo "Reset ($mode) complete."
