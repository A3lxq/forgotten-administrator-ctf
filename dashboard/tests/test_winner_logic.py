import time

from conftest import admin_login, claim_team


def test_live_winner_set_when_a_team_collects_every_genuine_flag(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})
    resp = client.post("/submit", data={"flag_value": "SYN{test_two}"})

    state = client.get("/leaderboard/state").get_json()
    assert state["live_winner"] == "Alpha"


def test_live_winner_does_not_change_once_set(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})
    client.post("/submit", data={"flag_value": "SYN{test_two}"})

    with client.application.test_client() as other:
        claim_team(other, "Beta", "5678")
        other.post("/submit", data={"flag_value": "SYN{test_one}"})
        other.post("/submit", data={"flag_value": "SYN{test_two}"})

    state = client.get("/leaderboard/state").get_json()
    assert state["live_winner"] == "Alpha"  # first past the post, not Beta


def test_no_live_winner_before_anyone_clears_all_genuine_flags(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})

    state = client.get("/leaderboard/state").get_json()
    assert state["live_winner"] is None


def test_end_event_sets_final_winner_by_highest_score(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})  # 100 pts

    with client.application.test_client() as other:
        claim_team(other, "Beta", "5678")
        other.post("/submit", data={"flag_value": "SYN{test_two}"})  # 150 pts

    admin_login(client)
    client.post("/admin/end-event")

    state = client.get("/leaderboard/state").get_json()
    assert state["final_winner"] == "Beta"
    assert state["event_ended"] is True


def test_end_event_tiebreak_favors_whoever_reached_the_score_first(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})  # Alpha: 100 first

    time.sleep(1.1)  # SQLite datetime('now') has 1-second resolution

    with client.application.test_client() as other:
        claim_team(other, "Beta", "5678")
        other.post("/submit", data={"flag_value": "SYN{test_one}"})  # Beta: 100 later

    admin_login(client)
    client.post("/admin/end-event")

    state = client.get("/leaderboard/state").get_json()
    assert state["final_winner"] == "Alpha"


def test_submissions_after_end_event_are_rejected(client):
    claim_team(client, "Alpha", "1234")
    admin_login(client)
    client.post("/admin/end-event")

    resp = client.post("/submit", data={"flag_value": "SYN{test_one}"})
    assert b"event has ended" in resp.data

    state = client.get("/leaderboard/state").get_json()
    assert state["event_ended"] is True
    assert state["standings"][0]["score"] == 0  # the post-end submission didn't score


def test_admin_routes_404_without_passcode_configured(app):
    app.config["ADMIN_PASSCODE"] = None
    with app.test_client() as c:
        resp = c.get("/admin/")
        assert resp.status_code == 404


def test_admin_requires_correct_passcode(client):
    resp = client.post("/admin/login", data={"passcode": "wrong"})
    assert b"Wrong passcode" in resp.data

    resp2 = client.get("/admin/")
    assert resp2.status_code == 302  # redirected to admin login, not authorized
