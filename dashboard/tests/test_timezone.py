import os
import time

from conftest import claim_team


def test_timestamps_use_system_local_time_not_utc(app, client):
    """Regression test for a real reported bug: datetime('now') in
    SQLite always returns UTC regardless of the host's timezone. Every
    DEFAULT/UPDATE in this project uses datetime('now', 'localtime')
    instead -- this proves it by actually changing the process
    timezone to something several hours off UTC and checking a fresh
    timestamp lands near the simulated local wall clock, not UTC."""
    original_tz = os.environ.get("TZ")
    try:
        os.environ["TZ"] = "Asia/Kolkata"  # UTC+5:30 -- large, unambiguous offset
        time.tzset()

        claim_team(client, "Alpha", "1234")

        with app.app_context():
            from app.db import get_db

            row = get_db().execute(
                "SELECT created_at FROM teams WHERE name = 'Alpha'"
            ).fetchone()
        stored = row["created_at"]

        import datetime as dt

        local_now = dt.datetime.now()
        utc_now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        stored_dt = dt.datetime.strptime(stored, "%Y-%m-%d %H:%M:%S")

        diff_from_local = abs((stored_dt - local_now).total_seconds())
        diff_from_utc = abs((stored_dt - utc_now).total_seconds())

        assert diff_from_local < 5, (
            f"stored timestamp {stored!r} should match simulated local "
            f"wall clock {local_now}, not drift by {diff_from_local}s"
        )
        # This is the actual regression check: UTC and local(+5:30) are
        # ~5.5 hours apart, so if the bug were present (UTC stored),
        # diff_from_utc would be tiny and diff_from_local would be ~19800s.
        assert diff_from_utc > 60, (
            "timestamp matches UTC almost exactly -- datetime('now') "
            "without 'localtime' has regressed"
        )
    finally:
        if original_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original_tz
        time.tzset()
