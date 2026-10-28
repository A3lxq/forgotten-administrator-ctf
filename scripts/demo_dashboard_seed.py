#!/usr/bin/env python3
"""demo_dashboard_seed.py -- populate a running dashboard with realistic
fake team activity, so you can see the leaderboard and score-over-time
chart actually working without powering up the CTF VM at all.

How this works without the VM: the dashboard validates submitted flag
strings against instructor-material/flag-manifest.json, not against
the live box -- the VM's only job in the real flow is to be the thing
players attack to *discover* those values. This script reads the real
flag values from that same manifest (the actual source of truth, not
hardcoded here) and submits them over HTTP to the dashboard's own
`/` and `/submit` routes -- the exact same code path a real player's
browser uses, just driven by several simulated "teams" instead of one
browser.

Usage:
    1. Start the dashboard first (separately, in another terminal):
         source .env && ./scripts/run-dashboard.sh
    2. Then run this:
         app/.venv/bin/python3 scripts/demo_dashboard_seed.py
       (any Python 3 works -- this only uses the standard library)

Safe to re-run: resubmitting a flag a team already has is a no-op (the
dashboard itself handles that), so running this twice without
resetting just adds nothing new rather than erroring. For a clean demo
each time, run `./scripts/reset-dashboard.sh` first.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "instructor-material" / "flag-manifest.json"
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://127.0.0.1:7000").rstrip("/")


def load_flags() -> dict[str, str]:
    """{flag_id: value} straight from the manifest -- the single source
    of truth this project already uses everywhere else."""
    data = json.loads(MANIFEST_PATH.read_text())
    return {f["id"]: f["value"] for f in data["flags"]}


def check_dashboard_up() -> None:
    try:
        with urllib.request.urlopen(f"{DASHBOARD_URL}/healthz", timeout=5) as r:
            if r.status != 200:
                raise RuntimeError(f"unexpected status {r.status}")
    except Exception as exc:
        print(f"Can't reach the dashboard at {DASHBOARD_URL} ({exc}).", file=sys.stderr)
        print("Start it first, in another terminal:", file=sys.stderr)
        print("  source .env && ./scripts/run-dashboard.sh", file=sys.stderr)
        print("(Or set DASHBOARD_URL if it's running somewhere else.)", file=sys.stderr)
        sys.exit(1)


class TeamSession:
    """One team's own cookie jar -- mirrors a real browser tab exactly,
    including the fact that each team only ever sees its own session."""

    def __init__(self, name: str, pin: str):
        self.name = name
        self.pin = pin
        cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def _post(self, path: str, data: dict) -> str:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(f"{DASHBOARD_URL}{path}", data=body, method="POST")
        with self.opener.open(req, timeout=10) as r:
            return r.read().decode()

    def join(self) -> None:
        self._post("/", {"team_name": self.name, "pin": self.pin})

    def submit(self, flag_value: str) -> str:
        html = self._post("/submit", {"flag_value": flag_value})
        if "Correct" in html:
            return "genuine"
        if "decoy" in html.lower():
            return "decoy"
        if "already submitted" in html:
            return "duplicate"
        return "invalid"


def main() -> None:
    check_dashboard_up()
    flags = load_flags()

    # (team name, pin, [flag ids to submit, in order]) -- a mix of fast/
    # slow teams and decoy detours so the leaderboard and chart both
    # show something worth looking at, not just one flat line.
    teams = [
        ("RedTeam", "demo1", ["original_flag_1", "original_flag_2", "original_flag_3",
                               "original_flag_4", "original_flag_5"]),
        ("BlueCrew", "demo2", ["original_flag_1", "d1a", "original_flag_2", "original_flag_3"]),
        ("GreenHats", "demo3", ["d2b", "original_flag_1", "original_flag_4"]),
        ("NightOwls", "demo4", ["original_flag_2", "original_flag_5"]),
        ("ZeroDay", "demo5", ["original_flag_1"]),
    ]

    print(f"Seeding {DASHBOARD_URL} with {len(teams)} demo teams...\n")

    sessions = {name: TeamSession(name, pin) for name, pin, _ in teams}
    for name, _, _ in teams:
        sessions[name].join()

    # Interleave submissions across teams (round-robin) with a short
    # real delay between each -- gives the score-over-time chart a
    # genuine, staggered shape instead of one instant burst, and lets
    # you watch /leaderboard update live while this runs if you have
    # it open already.
    queues = {name: list(flag_ids) for name, _, flag_ids in teams}
    while any(queues.values()):
        for name, _, _ in teams:
            if not queues[name]:
                continue
            flag_id = queues[name].pop(0)
            value = flags[flag_id]
            result = sessions[name].submit(value)
            print(f"  {name:<10} submits {flag_id:<16} -> {result}")
            time.sleep(1.5)

    print(
        f"\nDone. Open {DASHBOARD_URL}/leaderboard/ to see the live "
        f"leaderboard and score-over-time chart.\n"
        f"(RedTeam will show as the live winner -- it submitted all 5 "
        f"genuine flags.)\n"
        f"Reset before a real event or before re-running this for a "
        f"clean demo: ./scripts/reset-dashboard.sh"
    )


if __name__ == "__main__":
    main()
