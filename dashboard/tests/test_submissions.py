from conftest import claim_team


def test_submitting_a_genuine_flag_scores_points(client):
    claim_team(client)
    resp = client.post("/submit", data={"flag_value": "SYN{test_one}"})
    assert b"Correct" in resp.data
    assert b"100 points" in resp.data


def test_submitting_a_decoy_scores_zero(client):
    claim_team(client)
    resp = client.post("/submit", data={"flag_value": "FFLAG{test_decoy}"})
    assert b"decoy" in resp.data


def test_submitting_garbage_is_rejected(client):
    claim_team(client)
    resp = client.post("/submit", data={"flag_value": "not_a_flag_at_all"})
    assert b"Not a recognized flag" in resp.data


def test_resubmitting_the_same_flag_does_not_double_count(client):
    claim_team(client)
    client.post("/submit", data={"flag_value": "SYN{test_one}"})
    resp = client.post("/submit", data={"flag_value": "SYN{test_one}"})
    assert b"already submitted" in resp.data

    # Score should still be exactly 100, not 200.
    page = client.get("/submit")
    assert b"100 points" in page.data


def test_two_different_teams_can_both_score_the_same_genuine_flag(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})

    with client.application.test_client() as other:
        claim_team(other, "Beta", "5678")
        resp = other.post("/submit", data={"flag_value": "SYN{test_one}"})
        assert b"Correct" in resp.data


def test_leaderboard_state_reflects_submissions(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})

    resp = client.get("/leaderboard/state")
    data = resp.get_json()
    assert data["standings"][0]["name"] == "Alpha"
    assert data["standings"][0]["score"] == 100
    assert data["standings"][0]["genuine_found"] == 1
    assert data["standings"][0]["genuine_total"] == 2


def test_leaderboard_state_never_contains_raw_flag_values(client):
    claim_team(client)
    client.post("/submit", data={"flag_value": "SYN{test_one}"})

    resp = client.get("/leaderboard/state")
    assert b"SYN{test_one}" not in resp.data
