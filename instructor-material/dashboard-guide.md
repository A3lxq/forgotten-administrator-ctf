# Scoring Dashboard Guide

> Private — instructor use only (the `/admin` passcode is the one piece
> here that must stay that way; everything else is fine for players to
> see, by design).

## What this is

A self-service scoring dashboard for multi-team events: teams register
themselves, submit flags, see a live leaderboard, and get a confetti +
announcement moment both the instant a team clears all 5 genuine flags
and when you end the event. It replaces manually checking submissions
against `flag-manifest.json` yourself for every team.

It is a **completely separate application from the CTF VM** —
`dashboard/`, not `app/forgotten_admin/`. Run it on your own machine
(the same laptop hosting the CTF VM, just a different process/port), not
inside the VM. This is deliberate: the CTF VM is the thing teams get
shell and eventually root on by design, so scoring data has to live
somewhere that compromising the box can't reach. Nothing about this
dashboard changes the CTF VM, and nothing on the CTF VM can read or
write this dashboard's database.

It reads `instructor-material/flag-manifest.json` directly — the same
file that's already the single source of truth for every flag's value,
classification, and points. There's nothing to re-author; if you ever
regenerate flags with `scripts/author_flags.py`, just reload the
manifest from `/admin` (see below) rather than restarting the dashboard.

## One-time setup

**Already have this repo cloned?**
```
python3 -m venv dashboard/.venv
dashboard/.venv/bin/pip install -r dashboard/requirements.txt
```

**Just want the dashboard, not the whole repo (VM images, build
tooling, etc.)?** Grab the standalone package from
[Releases](https://github.com/A3lxq/forgotten-administrator-ctf/releases)
— tag `dashboard-vN` (separate from the `ova-export-vN` CTF VM
releases). It's self-contained: `dashboard/`, this guide, the flag
manifest, and the three `scripts/run-dashboard*.sh` wrappers, in the
same relative layout as the full repo. Extract it, then run the setup
command above from inside the extracted directory. **It includes
`instructor-material/flag-manifest.json`** (the dashboard needs it to
score flags) — that's the full answer key, so don't hand this specific
archive to players even though the repo itself is public.

## Starting it for an event

```
export DASHBOARD_ADMIN_PASSCODE='pick-something-only-you-know'
./scripts/run-dashboard.sh
```

- Binds to `0.0.0.0:7000` by default (override with `DASHBOARD_PORT`) so
  every player on the same LAN the CTF VM is already bridged onto can
  reach it — find this machine's own LAN IP (`ip addr` / `ifconfig`) and
  give players `http://<that-ip>:7000/`. (Not 6000: that port is on
  Chrome/Firefox's browser-blocked list, reserved for X11, and fails
  with `ERR_UNSAFE_PORT` in-browser even though the server itself is
  fine — found by testing this with a real browser.)
- **If `DASHBOARD_ADMIN_PASSCODE` isn't set, `/admin` 404s outright** —
  there's no default/fallback passcode shipped, on purpose. The public
  leaderboard and submission pages still work either way.
- Each run keeps its state in `dashboard/instance/dashboard.sqlite3`
  until you reset it (see below) — stopping and restarting the server
  does *not* clear scores.

## Event-day flow

1. Start the dashboard (above) before players arrive.
2. Give players the dashboard URL alongside the CTF VM's own address —
   they open the dashboard, pick a team name + PIN (first use creates
   the team; same two gets them back in later), and submit flags as
   they find them.
3. Point a projector/shared screen at `/leaderboard` — it updates on its
   own every few seconds, no refresh needed.
4. If any team collects all 5 genuine flags before time's up, the
   leaderboard fires confetti and announces them live, automatically —
   nothing for you to do.
5. When the event's time is up, sign in at `/admin` with your passcode
   and click **End Event**. This locks all further submissions and
   declares the final winner by score at that instant (ties broken by
   whoever reached that score first) — a second confetti/announcement
   moment fires on the leaderboard.
6. `/admin` also lists every team/submission, lets you remove a bogus
   or griefing team, and reload the flag manifest if you regenerated
   flags mid-setup.

## Resetting for a new run

```
./scripts/reset-dashboard.sh
```
Wipes all teams, submissions, and event state. Does **not** touch the
CTF VM or `flag-manifest.json` — only this dashboard's own database.
Run this between separate groups/classes, the same way you'd run
`./scripts/reset.sh vm` for the CTF box itself.

## What players never see

- Any flag value they haven't personally submitted (the leaderboard and
  every API response only ever show name/score/progress-count, never
  flag contents).
- `instructor-material/flag-manifest.json` itself — this dashboard
  reads it off disk at startup; it is never served over any route.
- Each other's PINs (hashed, same as the main CTF app's own web
  passwords — never stored or logged in plaintext).

## Running the dashboard's own tests

```
./scripts/run-dashboard-tests.sh
```
Covers flag classification, team claim/resume + PIN enforcement,
submission idempotency (resubmitting a flag doesn't double-score), and
both winner rules including the tie-break case.
