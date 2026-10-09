from forgotten_admin.db import get_db, seed_db


def test_health_check(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_seeded_users_exist(app):
    with app.app_context():
        db = get_db()
        usernames = {r["username"] for r in db.execute("SELECT username FROM users")}
    assert usernames == {"john", "admin"}


def test_seed_is_idempotent(app):
    """Running seed_db twice must not duplicate users or records
    (Section 19: setup scripts must be idempotent)."""
    with app.app_context():
        db = get_db()
        seed_db(db)  # second call
        seed_db(db)  # third call
        user_count = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        record_count = db.execute("SELECT COUNT(*) AS n FROM records").fetchone()["n"]
    assert user_count == 2
    assert record_count == 2
