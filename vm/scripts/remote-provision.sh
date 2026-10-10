#!/usr/bin/env bash
# remote-provision.sh — runs INSIDE the guest (invoked by provision.sh over
# SSH as ctfbuilder, with sudo). Idempotent: safe to re-run after the app
# code changes, after a reset, or after adding more flags in a later phase.
#
# What it does:
#   1. Lays out /opt/forgotten-admin (app code, owned by ctfbuilder:ctfbuilder,
#      not world-writable) and /opt/forgotten-admin/app/.venv (the app's
#      Python environment).
#   2. Sets the Linux "admin" account's password to match the web app's
#      seeded admin password, and enables SSH password auth for that
#      ONE account only (everyone else stays key-only/disabled). This
#      is Stage 4's intended "second vulnerability": password reuse
#      across the web app and the server itself. The IDOR disclosure
#      (Phase 2) is the entire exploit -- there is no separate
#      command-injection step anymore (an earlier build of this project
#      used one; removed by design in favor of this simpler, equally
#      realistic lesson).
#   2b. Creates the systemd service that runs the Flask app AS THE LINUX
#      "admin" ACCOUNT (not root, not ctfbuilder) -- narrative only now
#      (the app needing elevated internal access), not required for
#      the exploit path.
#   3. Lays out /home/admin/{README.txt,evidence,flags} per Section 11,
#      owned by admin, not world-readable.
#   4. Seeds the app's database (idempotent; db.py's seed_db() already
#      de-dupes).
set -euo pipefail

APP_DIR=/opt/forgotten-admin
VENV="$APP_DIR/app/.venv"

echo "== Installing OS packages =="
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip python3-cryptography >/dev/null

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

echo "== Syncing the Linux admin password to match the web app's (Stage 4) =="
# Same credential disclosed via the IDOR -- this reuse IS the exploit.
echo 'admin:N3tOps-Diag#7' | sudo chpasswd

echo "== Enabling SSH password auth for 'admin' only (everyone else stays key-only/disabled) =="
sudo tee /etc/ssh/sshd_config.d/90-admin-password-auth.conf >/dev/null <<'EOF'
# Loads after cloud-init's global "PasswordAuthentication no" (sorted
# after 50-/60-* by filename) and overrides it for this one account
# only -- intentional, Stage 4's credential-reuse lesson. john, root,
# and ctfbuilder are unaffected (root login is separately disabled;
# ctfbuilder/john have no business reason to use a password here).
Match User admin
    PasswordAuthentication yes
EOF
sudo chmod 644 /etc/ssh/sshd_config.d/90-admin-password-auth.conf
sudo sshd -t   # fail loudly here, not silently on the next SSH attempt
sudo systemctl reload ssh

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

echo "== Laying out player materials (Stage 1-3 content, served by the app) =="
PUBLIC_DATA_DIR=/opt/forgotten-admin/public-data
sudo mkdir -p "$PUBLIC_DATA_DIR"
sudo rsync -a --delete /tmp/forgotten-admin-public-data/ "$PUBLIC_DATA_DIR/"
sudo chown -R root:root "$PUBLIC_DATA_DIR"
sudo find "$PUBLIC_DATA_DIR" -type d -exec chmod 755 {} +
sudo find "$PUBLIC_DATA_DIR" -type f -exec chmod 644 {} +
sudo rm -rf /tmp/forgotten-admin-public-data

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
Environment=PUBLIC_DATA_DIR=$PUBLIC_DATA_DIR
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
sudo systemctl enable forgotten-admin.service
# `enable --now` does NOT restart an already-running service when the
# unit file or app code changed -- it's a no-op if it's already active.
# `restart` is unconditional and correct whether this is a first
# install or a re-provision after a code/config change.
sudo systemctl restart forgotten-admin.service
sleep 1
sudo systemctl --no-pager --full status forgotten-admin.service | head -10

echo "== Verifying the service runs as the Linux 'admin' account =="
RUN_USER=$(ps -o user= -C python3 | sort -u | grep -x admin || true)
if [ "$RUN_USER" != "admin" ]; then
  echo "WARNING: could not confirm the app process is running as 'admin'." >&2
fi

echo "== Installing the intended privilege-escalation weakness (Phase 5) =="
# Story: an "admin-tools" housekeeping cron job, group-writable because it
# was set up for both the app's deploy user and the admin account to be
# able to update it. INTENTIONAL WEAKNESS: it's writable by the `admin`
# group -- which the Linux `admin` account belongs to -- and root's cron
# runs it unmodified, every minute, as root. This is the one deliberate
# privesc path (Section 12): no other sudo/SUID/cron shortcut is added.
sudo mkdir -p /opt/admin-tools
sudo tee /opt/admin-tools/cleanup.sh >/dev/null <<'EOF'
#!/bin/bash
# Housekeeping for admin-tools cache (auto-generated by the deploy
# pipeline -- edits here are picked up by cron within a minute).
mkdir -p /var/cache/admin-tools
find /var/cache/admin-tools -type f -mtime +1 -delete 2>/dev/null
EOF
sudo chown root:admin /opt/admin-tools/cleanup.sh
sudo chmod 664 /opt/admin-tools/cleanup.sh   # group (admin) can WRITE this
sudo chmod 755 /opt/admin-tools

sudo touch /var/log/admin-tools-cleanup.log
sudo chown root:root /var/log/admin-tools-cleanup.log
sudo chmod 644 /var/log/admin-tools-cleanup.log

sudo tee /etc/cron.d/admin-tools-cleanup >/dev/null <<'EOF'
SHELL=/bin/bash
PATH=/usr/bin:/bin
* * * * * root bash /opt/admin-tools/cleanup.sh >> /var/log/admin-tools-cleanup.log 2>&1
EOF
sudo chmod 644 /etc/cron.d/admin-tools-cleanup
sudo systemctl restart cron

echo "== Verifying the privesc weakness is in place as intended =="
PERM=$(stat -c "%a %U:%G" /opt/admin-tools/cleanup.sh)
echo "cleanup.sh: $PERM (expected: 664 root:admin)"
sudo -u admin test -w /opt/admin-tools/cleanup.sh && echo "confirmed: admin CAN write cleanup.sh"
sudo -u admin test -w /etc/cron.d/admin-tools-cleanup && echo "WARNING: admin can also write the cron file itself (unintended)" || echo "confirmed: admin cannot write the cron definition (only the script it runs)"

echo "Done."
