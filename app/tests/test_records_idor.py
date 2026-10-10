"""Proves the intentional IDOR (Section 9 requirement):

- John can access his own record.
- John can access the admin's record purely by changing the id in the
  URL (the vulnerability).
- The admin record content (the "administrative resource") is revealed.
"""
from conftest import login


def test_john_can_access_own_record(app, client):
    from forgotten_admin.db import get_db

    with app.app_context():
        john_record_id = get_db().execute(
            "SELECT r.id FROM records r JOIN users u ON u.id = r.owner_user_id "
            "WHERE u.username = 'john'"
        ).fetchone()["id"]

    login(client, "john", "Summer2019!")
    resp = client.get(f"/records/{john_record_id}")
    assert resp.status_code == 200
    assert b"Handover notes" in resp.data


def test_john_can_access_admin_record_via_idor(app, client):
    from forgotten_admin.db import get_db

    with app.app_context():
        admin_record_id = get_db().execute(
            "SELECT r.id FROM records r JOIN users u ON u.id = r.owner_user_id "
            "WHERE u.username = 'admin'"
        ).fetchone()["id"]

    login(client, "john", "Summer2019!")
    # John requests a record id that is NOT his own.
    resp = client.get(f"/records/{admin_record_id}")

    # This assertion is the vulnerability check: in a fixed application
    # this would be 403/404, not 200 with admin's content.
    assert resp.status_code == 200
    assert b"Admin handover record" in resp.data
    assert b"N3tOps-Diag#7" in resp.data  # the reused admin credential


def test_anonymous_cannot_access_any_record(client):
    resp = client.get("/records/1", follow_redirects=False)
    assert resp.status_code == 302
