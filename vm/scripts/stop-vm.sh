#!/usr/bin/env bash
# stop-vm.sh — shuts the VM down cleanly (QMP system_powerdown), falling
# back to a process kill only if it doesn't stop in time. Never touches
# anything on the host outside this VM's own pidfile/monitor socket.
set -euo pipefail
cd "$(dirname "$0")/.."

PIDFILE="disks/vm.pid"
MONITOR="disks/monitor.sock"

if [ ! -f "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "VM is not running."
  rm -f "$PIDFILE"
  exit 0
fi

PID="$(cat "$PIDFILE")"

if [ -S "$MONITOR" ] && command -v socat >/dev/null 2>&1; then
  echo "system_powerdown" | socat - "UNIX-CONNECT:$MONITOR" >/dev/null 2>&1 || true
  for _ in $(seq 1 30); do
    kill -0 "$PID" 2>/dev/null || { echo "VM shut down cleanly."; rm -f "$PIDFILE"; exit 0; }
    sleep 1
  done
  echo "Clean shutdown timed out; terminating process $PID." >&2
fi

kill "$PID" 2>/dev/null || true
sleep 2
kill -0 "$PID" 2>/dev/null && kill -9 "$PID" 2>/dev/null || true
rm -f "$PIDFILE"
echo "VM stopped."
