from conftest import login


def test_login_required_for_records(client):
    resp = client.get("/records/1", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_john_login_succeeds(client):
    resp = login(client, "john", "Summer2019!")
    assert resp.status_code == 302  # redirected to their own record


def test_admin_login_succeeds(client):
    resp = login(client, "admin", "N3tOps-Diag#7")
    assert resp.status_code == 302


def test_wrong_password_fails(client):
    resp = login(client, "john", "not-the-password")
    assert resp.status_code == 200  # re-renders login form
    assert b"Invalid username or password" in resp.data
