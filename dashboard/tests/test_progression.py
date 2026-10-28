from conftest import claim_team


def test_progression_empty_when_no_teams(client):
    resp = client.get("/leaderboard/progression")
    assert resp.status_code == 200
    assert resp.get_json() == {"series": []}


def test_progression_tracks_cumulative_score(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})  # +100
    client.post("/submit", data={"flag_value": "SYN{test_two}"})  # +150

    data = client.get("/leaderboard/progression").get_json()
    alpha = next(s for s in data["series"] if s["name"] == "Alpha")
    assert [p["score"] for p in alpha["points"]] == [100, 250]


def test_progression_includes_decoys_as_zero_point_steps(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})  # +100
    client.post("/submit", data={"flag_value": "FFLAG{test_decoy}"})  # +0

    data = client.get("/leaderboard/progression").get_json()
    alpha = next(s for s in data["series"] if s["name"] == "Alpha")
    assert [p["score"] for p in alpha["points"]] == [100, 100]


def test_progression_never_exposes_flag_values(client):
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})

    resp = client.get("/leaderboard/progression")
    assert b"SYN{test_one}" not in resp.data


def test_progression_has_one_series_per_team(client):
    claim_team(client, "Alpha", "1234")
    with client.application.test_client() as other:
        claim_team(other, "Beta", "5678")

    data = client.get("/leaderboard/progression").get_json()
    names = sorted(s["name"] for s in data["series"])
    assert names == ["Alpha", "Beta"]


def test_back_to_back_submissions_get_genuinely_distinct_timestamps(client):
    """Regression test for a real reported bug: two flags submitted
    back-to-back (no delay) used to land in the same SQLite second
    (datetime('now', 'localtime') only has 1-second resolution), so
    both points on the progression chart collapsed to the exact same
    x-position and rendered as a near-invisible sliver at the edge --
    the user reported this as "the graph is not showing". Timestamps
    now use strftime(..., '%f', ...) for millisecond precision, so
    even submissions in the same second are distinguishable."""
    claim_team(client, "Alpha", "1234")
    client.post("/submit", data={"flag_value": "SYN{test_one}"})
    client.post("/submit", data={"flag_value": "SYN{test_two}"})

    data = client.get("/leaderboard/progression").get_json()
    alpha = next(s for s in data["series"] if s["name"] == "Alpha")
    timestamps = [p["t"] for p in alpha["points"]]
    assert timestamps[0] != timestamps[1], (
        "both submissions got the identical timestamp -- millisecond "
        "precision has regressed back to 1-second SQLite granularity"
    )
    assert "." in timestamps[0], "timestamp has no fractional-second part"
