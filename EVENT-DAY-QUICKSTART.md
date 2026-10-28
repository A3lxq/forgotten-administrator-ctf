# Event-Day Quickstart — Instructor Setup

The complete instructor setup, start to finish — both pieces run on
your own laptop, nothing on the CTF VM itself hosts the dashboard.

**Prerequisites on this machine**: VirtualBox (or VMware) for the CTF
box, and Python 3.10+ with `pip` for the dashboard. Nothing else —
each piece is otherwise self-contained (see "Get the code" below).

## Part A — The vulnerable CTF box

1. **Download and verify** the latest OVA (`ova-export-v6`) from
   [Releases](https://github.com/A3lxq/forgotten-administrator-ctf/releases/tag/ova-export-v6):
   ```
   sha256sum -c forgotten-admin-ctf.ova.sha256
   ```
2. **Import into VirtualBox**, dry-run first:
   ```
   VBoxManage import forgotten-admin-ctf.ova --dry-run
   VBoxManage import forgotten-admin-ctf.ova
   ```
3. **Pick a network mode** before powering on (`SETUP.md`):
   - **Solo/testing** → NAT + port-forward guest `8000`→some host port.
   - **Real multi-team event** → **Bridged Adapter** on your actual
     workshop LAN interface. DHCP and all services already support
     this (no extra config). Only ever do this on a LAN you control —
     never shared/public Wi-Fi.
4. **Power on**, give it a minute to boot.
5. **Take a VirtualBox snapshot now, before any player touches it** —
   this is how you reset between groups/classes later (`scripts/reset.sh
   vm` is for the project's own QEMU dev build, not a VirtualBox
   import, so it won't work here):
   ```
   VBoxManage snapshot "forgotten-admin-ctf" take clean-start
   ```
   (VM name may differ if you renamed it on import — check
   `VBoxManage list vms` if unsure.) To reset later: power the VM off,
   restore that snapshot, power back on:
   ```
   VBoxManage controlvm "forgotten-admin-ctf" poweroff
   VBoxManage snapshot "forgotten-admin-ctf" restore clean-start
   VBoxManage startvm "forgotten-admin-ctf"
   ```
   Or via the GUI: Machine → Tools → Snapshots → right-click
   `clean-start` → Restore.
6. **Find its address**: for Bridged, open the VirtualBox console
   window (not SSH) and log in as `john`/`Summer2019!` or
   `admin`/`N3tOps-Diag#7`, then run `hostname -I` — that's the CTF
   box's own IP on your LAN.
7. **Give players**: just that IP. Everything else — materials, the
   decrypt tool, Rules/Flag-Submission docs — is served by the box
   itself at `/`. For a single document to hand out (print, paste into
   a chat, whatever's easiest), `player-material/Player-Handout.md` has
   it all in one place — the `john`/`Summer2019!` web login, rules, and
   scoring — instead of pointing them at the individual files.
8. Keep `instructor-material/credentials.md` handy for yourself —
   `ctfbuilder` SSH access and direct troubleshooting, bypassing the
   CTF entirely. (If you only downloaded the OVA and haven't cloned
   the repo, [view it on GitHub](https://github.com/A3lxq/forgotten-administrator-ctf/blob/master/instructor-material/credentials.md)
   instead — note that `ctfbuilder`'s SSH key itself still isn't
   shipped with the OVA either way, by design; only the console
   `john`/`admin` logins from step 6 work for a downloaded OVA you
   didn't build yourself.)

## Part B — The scoring dashboard

Runs as a **separate process on this same laptop** — deliberately not
on the VM, so a team that roots the box still can't touch scores.

1. **Get the code.** Either clone the full repo:
   ```
   git clone https://github.com/A3lxq/forgotten-administrator-ctf.git
   cd forgotten-administrator-ctf
   ```
   or, if you just want the dashboard and not the VM build tooling,
   grab the newest standalone `dashboard-vN` package from
   [Releases](https://github.com/A3lxq/forgotten-administrator-ctf/releases)
   and extract it instead — same commands below either way, run from
   inside whichever directory you end up in.
2. **One-time setup**:
   ```
   python3 -m venv dashboard/.venv
   dashboard/.venv/bin/pip install -r dashboard/requirements.txt
   ```
3. **Create your own admin passcode + a stable login key, and start
   it** — the passcode gates `/admin`; the key keeps everyone logged
   in if the dashboard ever has to restart (power outage, crash) —
   without it, a restart logs every team out (their scores are safe
   either way, just not the logins):
   ```
   {
     echo "export DASHBOARD_ADMIN_PASSCODE='pick-something-only-you-know'"
     echo "export DASHBOARD_SECRET_KEY='$(python3 -c "import secrets; print(secrets.token_hex(32))")'"
   } > .env
   source .env
   ./scripts/run-dashboard.sh
   ```
   `.env` is already in `.gitignore` if you're in the full repo clone
   (never commit it — this repo is public); if you extracted the
   standalone release instead, there's no `.gitignore` to rely on, so
   just keep that directory itself private. Every time you restart the
   dashboard later, `source .env` again before `run-dashboard.sh` —
   nothing in it is saved anywhere else between runs, and reusing the
   same `.env` is exactly what keeps everyone's login intact across
   that restart. Binds to `0.0.0.0:7000`.
4. **Find this machine's own LAN IP** (`ip addr` / `ifconfig` — note:
   this is the *host's* IP, different from the VM's bridged IP from
   Part A, since they're two separate network presences on the same
   LAN). Give players `http://<host-ip>:7000/`.
5. **Players**: pick a team name + PIN once, then submit flags as they
   find them. Leaderboard at `/leaderboard` — good to put on a
   projector.
6. **You**: sign in at `/admin` with the passcode for team management,
   and click **End Event** when time's up (locks submissions, declares
   the final winner).

## Running the actual event

- Start both (VM + dashboard) before players arrive; hand out both
  addresses together.
- Project `/leaderboard` — it updates live, confetti fires
  automatically when a team clears all 5 flags and again when you end
  the event.
- Help players per `player-material/Rules.md` (asking you for a hint
  is allowed).
- When time's up: `/admin` → **End Event**.
- Between separate groups/classes: restore the `clean-start`
  VirtualBox snapshot (Part A, step 5) for the CTF box,
  `./scripts/reset-dashboard.sh` (or the admin **Reset** button) for
  the dashboard — both independent, reset either without touching the
  other. (`scripts/reset.sh vm` only applies if you built the VM
  yourself from source with the project's QEMU tooling — not to a
  VirtualBox-imported OVA, which is the path this guide actually
  walks through.)

Full reference docs if you want more detail on any piece: `SETUP.md`
(box), `instructor-material/instructor-guide.md` (running the event),
`instructor-material/dashboard-guide.md` (dashboard specifics).
