# Event-Day Quickstart — Instructor Setup

The complete instructor setup, start to finish — both pieces run on
your own laptop, nothing on the CTF VM itself hosts the dashboard.

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
5. **Find its address**: for Bridged, open the VirtualBox console
   window (not SSH) and log in as `john`/`Summer2019!` or
   `admin`/`N3tOps-Diag#7`, then run `hostname -I` — that's the CTF
   box's own IP on your LAN.
6. **Give players**: just that IP. Everything else — materials, the
   decrypt tool, Rules/Flag-Submission docs — is served by the box
   itself at `/`. `player-material/Getting-Started.md` is what they
   see; it hands them the `john`/`Summer2019!` web login directly.
7. Keep `instructor-material/credentials.md` handy for yourself —
   `ctfbuilder` SSH access and direct troubleshooting, bypassing the
   CTF entirely.

## Part B — The scoring dashboard

Runs as a **separate process on this same laptop** — deliberately not
on the VM, so a team that roots the box still can't touch scores.

1. **Get the code** — either you already have the full repo, or grab
   the standalone `dashboard-v2` release if you ever need it on a
   different machine without the whole project.
2. **One-time setup**:
   ```
   python3 -m venv dashboard/.venv
   dashboard/.venv/bin/pip install -r dashboard/requirements.txt
   ```
3. **Set the admin passcode and start it.** A `.env` file at the repo
   root already holds the real event passcode on this machine — create
   it once like this (never commit it; this repo is public):
   ```
   echo "export DASHBOARD_ADMIN_PASSCODE='pick-something-only-you-know'" > .env
   ```
   `.env` is already in `.gitignore`, so it's safe to keep here. Then,
   every time you start the dashboard:
   ```
   source .env
   ./scripts/run-dashboard.sh
   ```
   Binds to `0.0.0.0:7000`.
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
- Between separate groups/classes: `./scripts/reset.sh vm` for the CTF
  box, `./scripts/reset-dashboard.sh` (or the admin **Reset** button)
  for the dashboard — both independent, reset either without touching
  the other.

Full reference docs if you want more detail on any piece: `SETUP.md`
(box), `instructor-material/instructor-guide.md` (running the event),
`instructor-material/dashboard-guide.md` (dashboard specifics).
