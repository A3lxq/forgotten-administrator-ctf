#!/usr/bin/env bash
# remote-provision.sh — runs INSIDE the guest (invoked by provision.sh over
# SSH as ctfbuilder, with sudo). Idempotent: safe to re-run after the app
# code changes, after a reset, or after adding more flags in a later phase.
#
# What it does:
#   1. Lays out /opt/forgotten-admin (app code, owned by ctfbuilder:ctfbuilder,
#      not world-writable) and /opt/forgotten-admin/app/.venv (the app's
#      Python environment).
#   2. Creates the systemd service that runs the Flask app AS THE LINUX
#      "admin" ACCOUNT (not root, not ctfbuilder) -- this is what makes the
#      app's own admin-diagnostics command injection (Phase 2) translate
#      into real code execution as the Linux admin user.
#   3. Lays out /home/admin/{README.txt,evidence,flags} per Section 11,
#      owned by admin, not world-readable.
#   4. Seeds the app's database (idempotent; db.py's seed_db() already
#      de-dupes).
set -euo pipefail

APP_DIR=/opt/forgotten-admin
VENV="$APP_DIR/app/.venv"

echo "== Installing OS packages =="
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip >/dev/null

echo "== Laying out $APP_DIR =="
sudo mkdir -p "$APP_DIR"
sudo chown ctfbuilder:ctfbuilder "$APP_DIR"
sudo rsync -a --delete \
  --exclude ".venv" --exclude "__pycache__" --exclude "instance" --exclude ".pytest_cache" \
  /tmp/forgotten-admin-app/ "$APP_DIR/app/"

echo "== Creating app virtualenv =="
if [ ! -x "$VENV/bin/python3" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q -r "$APP_DIR/app/requirements.txt"

echo "== Seeding database =="
FLASK_APP="$APP_DIR/app/wsgi.py" "$VENV/bin/flask" seed || true

echo "== Laying out /home/admin evidence directories (Section 11) =="
sudo -u admin mkdir -p /home/admin/evidence /home/admin/flags
sudo -u admin tee /home/admin/README.txt >/dev/null <<'EOF'
ADMINISTRATOR'S NOTE

If you are reading this, you have recovered access to the administrator's
environment.

The web application was only the first boundary.

The final evidence was moved to the root account after the last security
review.

The repository contains a credential required to unlock the final
evidence.

Investigate the system, identify the intended path to root, and recover
the final artifact.
EOF
sudo chmod 750 /home/admin /home/admin/evidence /home/admin/flags
sudo chown -R admin:admin /home/admin

echo "== Installing systemd service (runs as Linux 'admin', not root) =="
sudo tee /etc/systemd/system/forgotten-admin.service >/dev/null <<EOF
[Unit]
Description=Forgotten Administrator CTF web app (Stage 4)
After=network.target

[Service]
Type=simple
User=admin
Group=admin
WorkingDirectory=$APP_DIR/app
Environment=FLASK_APP=$APP_DIR/app/wsgi.py
ExecStart=$VENV/bin/python3 $APP_DIR/app/wsgi.py
Restart=on-failure
# Deliberately NOT root, NOT NoNewPrivileges=false-with-caps, no extra
# capabilities -- the app runs with exactly the "admin" account's own
# privileges, nothing more.

[Install]
WantedBy=multi-user.target
EOF

# The app's dev entry point binds to 127.0.0.1 by default; override for
# the VM so it's reachable via the hostfwd (still guest-local, no bridge).
sudo sed -i "s/app.run(debug=False)/app.run(host='0.0.0.0', port=8000, debug=False)/" "$APP_DIR/app/wsgi.py"

sudo systemctl daemon-reload
sudo systemctl enable --now forgotten-admin.service
sleep 1
sudo systemctl --no-pager --full status forgotten-admin.service | head -10

echo "== Verifying the service runs as the Linux 'admin' account =="
RUN_USER=$(ps -o user= -C python3 | sort -u | grep -x admin || true)
if [ "$RUN_USER" != "admin" ]; then
  echo "WARNING: could not confirm the app process is running as 'admin'." >&2
fi

echo "Done."
