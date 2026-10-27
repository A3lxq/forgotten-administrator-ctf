from conftest import claim_team


def test_claiming_a_new_team_succeeds(client):
    resp = claim_team(client, "Alpha", "1234")
    assert resp.status_code == 200
    assert b"Submit a flag" in resp.data


def test_short_pin_rejected(client):
    resp = client.post("/", data={"team_name": "Alpha", "pin": "12"})
    assert b"PIN must be at least" in resp.data


def test_empty_name_rejected(client):
    resp = client.post("/", data={"team_name": "", "pin": "1234"})
    assert b"can" in resp.data and b"be empty" in resp.data


def test_resuming_with_wrong_pin_is_rejected(client):
    claim_team(client, "Alpha", "1234")
    # A second, independent client (no shared session/cookies) tries to
    # resume the same team name with the wrong PIN.
    with client.application.test_client() as other:
        resp = other.post("/", data={"team_name": "Alpha", "pin": "wrong"})
        assert b"match it" in resp.data


def test_resuming_with_correct_pin_from_a_new_session_succeeds(client):
    claim_team(client, "Alpha", "1234")
    with client.application.test_client() as other:
        resp = other.post(
            "/", data={"team_name": "Alpha", "pin": "1234"}, follow_redirects=True
        )
        assert resp.status_code == 200
        assert b"Alpha" in resp.data


def test_submit_requires_a_team_session(client):
    resp = client.get("/submit", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
