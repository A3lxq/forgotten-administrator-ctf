from conftest import admin_login, claim_team


def test_reset_requires_admin(client):
    claim_team(client, "Alpha", "1234")
    resp = client.post("/admin/reset", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]

    # The team is untouched -- an unauthorized reset attempt did nothing.
    state = client.get("/leaderboard/state").get_json()
    assert state["standings"][0]["name"] == "Alpha"


def test_reset_wipes_teams_submissions_and_event_state(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})
    client.post("/submit", data={"flag_value": "SYN{test_two}"})  # triggers live winner

    admin_login(client)
    client.post("/admin/end-event")  # sets ended_at + final winner too

    pre_state = client.get("/leaderboard/state").get_json()
    assert pre_state["live_winner"] == "Alpha"
    assert pre_state["final_winner"] == "Alpha"
    assert pre_state["event_ended"] is True

    client.post("/admin/reset")

    post_state = client.get("/leaderboard/state").get_json()
    assert post_state["standings"] == []
    assert post_state["live_winner"] is None
    assert post_state["final_winner"] is None
    assert post_state["event_ended"] is False


def test_a_teams_old_session_cannot_submit_after_a_reset(client):
    """A team's browser still has its session cookie after an instructor
    reset -- that must not let them keep submitting as a now-deleted
    team row (and must not 500 either)."""
    claim_team(client, "Alpha", "1234")

    with client.application.test_client() as admin_client:
        admin_login(admin_client)
        admin_client.post("/admin/reset")

    resp = client.get("/submit", follow_redirects=False)
    assert resp.status_code == 302  # bounced back to claim, not a crash

    resp2 = client.post("/submit", data={"flag_value": "SYN{test_one}"}, follow_redirects=False)
    assert resp2.status_code == 302


def test_after_reset_a_fresh_event_can_be_scored_normally(client):
    claim_team(client, "Alpha", "1234")
    admin_login(client)
    client.post("/admin/end-event")
    client.post("/admin/reset")

    # Same browser, re-claims the same team name (it's free again) and
    # scores normally -- reset didn't leave the DB in a broken state.
    with client.application.test_client() as fresh:
        claim_team(fresh, "Alpha", "1234")
        resp = fresh.post("/submit", data={"flag_value": "SYN{test_one}"})
        assert b"Correct" in resp.data

    state = client.get("/leaderboard/state").get_json()
    assert state["standings"][0]["score"] == 100
    assert state["event_ended"] is False
