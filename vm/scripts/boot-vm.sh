#!/usr/bin/env bash
# boot-vm.sh — starts the CTF VM in the background with host-only
# networking (QEMU user-mode NAT). No bridge, no public exposure.
#
# Port mapping (host -> guest), bound to 127.0.0.1 only by default:
#   127.0.0.1:2222 -> guest:22   (SSH, instructor/ctfbuilder only)
#   127.0.0.1:8080 -> guest:8000 (the vulnerable web app, Stage 4)
# Port 8000, not 80, so the app never needs a privileged bind inside
# the guest (it runs as the unprivileged "admin" account, not root).
#
# See vm/networking.md for what this means for players on a separate
# lab network vs. this single-host development setup.
set -euo pipefail
cd "$(dirname "$0")/.."

DISK="disks/forgotten-admin.qcow2"
SEED="seed/seed.img"
PIDFILE="disks/vm.pid"
MONITOR="disks/monitor.sock"
LOG="../logs/vm-console.log"

if [ ! -f "$DISK" ] || [ ! -f "$SEED" ]; then
  echo "Missing $DISK or $SEED. Run ./scripts/create-disk.sh first." >&2
  exit 1
fi

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "VM already running (pid $(cat "$PIDFILE"))." >&2
  exit 1
fi

mkdir -p ../logs

ACCEL="tcg"
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
  ACCEL="kvm"
fi
echo "Using acceleration: $ACCEL"

qemu-system-x86_64 \
  -name forgotten-admin \
  -machine type=q35,accel=$ACCEL \
  -cpu max \
  -m 2048 \
  -smp 2 \
  -drive file="$DISK",if=virtio,format=qcow2 \
  -drive file="$SEED",if=virtio,format=raw \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22,hostfwd=tcp:127.0.0.1:8080-:8000 \
  -device virtio-net-pci,netdev=net0 \
  -display none \
  -serial file:"$LOG" \
  -monitor unix:"$MONITOR",server,nowait \
  -pidfile "$PIDFILE" \
  -daemonize

echo "VM starting (pid $(cat "$PIDFILE"))."
echo "Console log: vm/$LOG"
echo "SSH (instructor only, once boot completes):"
echo "  ssh -i keys/ctfbuilder_ed25519 -p 2222 ctfbuilder@127.0.0.1"
echo "Web app (once deployed): http://127.0.0.1:8080/"
echo "Stop with: ./scripts/stop-vm.sh"
