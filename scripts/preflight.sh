#!/usr/bin/env bash
# preflight.sh — checks the host has what later scripts need. Safe to run
# any number of times; it only reads state, never changes anything.
set -euo pipefail

status=0
check() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "[ OK ] $desc"
    else
        echo "[MISS] $desc"
        status=1
    fi
}

echo "== Forgotten Administrator CTF — preflight =="
check "python3 available"        command -v python3
check "git available"            command -v git
check "openssl available"       command -v openssl
check "docker available (optional, dev-only)" command -v docker
check "qemu-system-x86_64 available (needed for Phase 3 VM build)" command -v qemu-system-x86_64
check "qemu-img available (needed for Phase 3 VM build)" command -v qemu-img
check "cloud-localds available (needed for Phase 3 VM build)" command -v cloud-localds
check "exiftool available (needed for Phase 4 metadata files)" command -v exiftool

if [ "$status" -ne 0 ]; then
    echo
    echo "Some tools are missing. See DEPENDENCIES.md for the install command."
    echo "This script does NOT install anything itself (no sudo calls)."
fi

exit "$status"
