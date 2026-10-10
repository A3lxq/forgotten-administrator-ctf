#!/usr/bin/env bash
# health-check.sh — safe, read-only checks that the VM and app are up
# and correctly isolated. Never modifies anything.
set -uo pipefail
cd "$(dirname "$0")/.."

KEY="vm/keys/ctfbuilder_ed25519"
SSH="ssh -i $KEY -p 2222 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 ctfbuilder@127.0.0.1"
status=0

check() {
  local desc="$1"; shift
  if "$@" >/tmp/health-check-out.$$ 2>&1; then
    echo "[ OK ] $desc"
  else
    echo "[FAIL] $desc"
    sed 's/^/       /' /tmp/health-check-out.$$
    status=1
  fi
  rm -f /tmp/health-check-out.$$
}

echo "== Forgotten Administrator CTF — health check =="

check "VM reachable over SSH (instructor key)" bash -c "$SSH 'echo ok' | grep -q ok"
check "web app /healthz returns ok" bash -c "curl -sf http://127.0.0.1:8080/healthz | grep -q '\"status\":\"ok\"'"
check "player materials reachable unauthenticated (Stage 1-3, no handout folder needed)" bash -c "
  curl -sf http://127.0.0.1:8080/materials/osint/profile.html | grep -q jtyler_dev &&
  curl -sf http://127.0.0.1:8080/materials/stage3-git-history.tar.gz -o /dev/null
"
check "materials route rejects path traversal" bash -c "
  code=\$(curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:8080/materials/osint/../../app/forgotten_admin/db.py')
  [ \"\$code\" = '404' ]
"
check "forgotten-admin.service is active" bash -c "$SSH 'systemctl is-active forgotten-admin' | grep -q active"
check "app runs as Linux 'admin', not root" bash -c "$SSH 'ps -o user= -C python3' | grep -qx admin"
check "admin has no sudo rights" bash -c "$SSH 'sudo -u admin sudo -n -l' 2>&1 | grep -q 'password is required'"
check "root login is disabled" bash -c "$SSH 'sudo passwd -S root' | grep -qE ' L | NP '"
check "only expected ports are listening" bash -c "
  out=\$($SSH 'sudo ss -tlnp' 2>/dev/null)
  echo \"\$out\" | grep -q ':22 ' && echo \"\$out\" | grep -q ':8000 ' || exit 1
  unexpected=\$(echo \"\$out\" | grep -vE ':22 |:8000 |:53 |State' || true)
  [ -z \"\$unexpected\" ]
"
check "privesc weakness is in its expected state (writable by admin group)" bash -c "$SSH 'sudo -u admin test -w /opt/admin-tools/cleanup.sh'"
check "/root is not readable by admin" bash -c "! $SSH 'sudo -u admin test -r /root/final_evidence.enc'"

echo
if [ "$status" -eq 0 ]; then
  echo "RESULT: healthy"
else
  echo "RESULT: one or more checks failed"
fi
exit "$status"
