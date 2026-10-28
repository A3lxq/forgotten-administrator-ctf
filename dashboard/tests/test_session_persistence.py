import json

from conftest import TEST_FLAGS, admin_login, claim_team


def _make_app_factory(tmp_path, secret_key):
    """Builds a fresh app instance against the SAME db/manifest files,
    simulating the dashboard process restarting -- a real restart is
    exactly 'the old process dies, a new one starts, same files on
    disk, config read fresh'."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app import create_app

    db_path = tmp_path / "test.sqlite3"
    manifest_path = tmp_path / "flag-manifest.json"
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps(TEST_FLAGS))

    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "FLAG_MANIFEST_PATH": str(manifest_path),
            "ADMIN_PASSCODE": "test-passcode",
            "SECRET_KEY": secret_key,
        }
    )
    from app.db import get_db, init_db

    with app.app_context():
        init_db(get_db())
    return app


def _raw_session_cookie(client) -> str:
    """The literal Set-Cookie value, so it can be replayed against a
    DIFFERENT app/client -- unlike session_transaction(), which injects
    session data directly and never actually exercises the signature
    verification a real cross-process cookie replay depends on."""
    cookie = client.get_cookie("session")
    if cookie is None:
        raise AssertionError("no session cookie was set")
    return cookie.value


def test_session_survives_a_simulated_restart_with_a_stable_secret_key(tmp_path):
    """The actual regression this fixes: a team logs in, the dashboard
    process restarts (new app instance, same db file, same configured
    secret key), and the team should still be logged in afterward --
    no re-entering their name/PIN. Uses the REAL signed cookie value
    (not session_transaction(), which bypasses signature verification
    entirely) so this genuinely proves cross-process validity."""
    stable_key = "a-stable-key-set-once-in-.env"

    app1 = _make_app_factory(tmp_path, stable_key)
    client1 = app1.test_client()
    claim_team(client1, "Alpha", "1234")
    raw_cookie = _raw_session_cookie(client1)

    # Simulate a restart: a brand-new app object, same secret key, same db.
    app2 = _make_app_factory(tmp_path, stable_key)
    client2 = app2.test_client()
    client2.set_cookie("session", raw_cookie, domain="localhost")

    resp = client2.get("/submit")
    assert resp.status_code == 200  # not redirected to claim -- still logged in
    assert b"Alpha" in resp.data


def test_session_does_not_survive_a_restart_with_a_different_secret_key(tmp_path):
    """Confirms the mechanism actually depends on the key being stable
    -- without that, a restart (a genuinely different key, matching
    the old random-per-process fallback) must still log teams out, so
    this is a meaningful fix and not a no-op."""
    app1 = _make_app_factory(tmp_path, "key-one")
    client1 = app1.test_client()
    claim_team(client1, "Alpha", "1234")
    raw_cookie = _raw_session_cookie(client1)

    app2 = _make_app_factory(tmp_path, "a-completely-different-key")
    client2 = app2.test_client()
    client2.set_cookie("session", raw_cookie, domain="localhost")

    resp = client2.get("/submit", follow_redirects=False)
    assert resp.status_code == 302  # bounced to claim -- session didn't carry over


def test_team_session_is_permanent(client):
    claim_team(client, "Alpha", "1234")
    with client.session_transaction() as sess:
        assert sess.permanent is True


def test_admin_session_is_permanent(client):
    admin_login(client)
    with client.session_transaction() as sess:
        assert sess.permanent is True
