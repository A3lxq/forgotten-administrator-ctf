from conftest import admin_login, claim_team


def test_team_can_post_and_see_own_message(client):
    claim_team(client, "Alpha", "1234")
    resp = client.post("/hints", data={"body": "How do I find flag 2?"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"How do I find flag 2?" in resp.data


def test_empty_message_rejected(client):
    claim_team(client, "Alpha", "1234")
    resp = client.post("/hints", data={"body": "   "})
    assert b"Type a question first" in resp.data


def test_overlong_message_rejected(client):
    claim_team(client, "Alpha", "1234")
    resp = client.post("/hints", data={"body": "x" * 2001})
    assert b"Keep it under" in resp.data


def test_hints_requires_a_team_session(client):
    resp = client.get("/hints", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


# --- The critical property: strict team <-> admin isolation ---


def test_team_a_cannot_see_team_bs_messages(client):
    """There is no route that lets a team view another team's thread --
    /hints is always scoped to the logged-in team's own session. This
    test proves it structurally: team A posts a message, team B's own
    /hints and /hints/state responses never contain it."""
    claim_team(client, "Alpha", "1234")
    client.post("/hints", data={"body": "Alpha's secret question"})

    with client.application.test_client() as other:
        claim_team(other, "Beta", "5678")
        page = other.get("/hints")
        assert b"Alpha's secret question" not in page.data

        state = other.get("/hints/state").get_json()
        bodies = [m["body"] for m in state["messages"]]
        assert "Alpha's secret question" not in bodies
        assert state["messages"] == []  # Beta has sent nothing of its own either


def test_team_facing_routes_never_accept_a_team_id_parameter(client):
    """Confirms there's no way to even attempt cross-team access via a
    URL parameter -- /hints takes no id at all, unlike the admin-only
    /admin/hints/<team_id>."""
    claim_team(client, "Alpha", "1234")
    # Only the admin blueprint has a per-team URL; hitting that path
    # without admin auth must not leak anything either.
    resp = client.get("/admin/hints/1", follow_redirects=False)
    assert resp.status_code in (302, 404)  # bounced to admin login, not shown


def test_admin_sees_the_message_and_can_reply(client):
    claim_team(client, "Alpha", "1234")
    client.post("/hints", data={"body": "Stuck on stage 3"})

    admin_login(client)
    inbox = client.get("/admin/hints")
    assert b"Stuck on stage 3" in inbox.data
    assert b"waiting" in inbox.data.lower()

    # Alpha is the first team created in this test's fresh DB -> id 1.
    reply = client.post(
        "/admin/hints/1", data={"body": "Check the EXIF data"}, follow_redirects=True
    )
    assert b"Check the EXIF data" in reply.data


def test_team_sees_admin_reply(client):
    claim_team(client, "Alpha", "1234")
    client.post("/hints", data={"body": "Stuck on stage 3"})

    with client.application.test_client() as admin_client:
        admin_login(admin_client)
        admin_client.post("/admin/hints/1", data={"body": "Check the EXIF data"})

    page = client.get("/hints")
    assert b"Check the EXIF data" in page.data

    state = client.get("/hints/state").get_json()
    senders = [m["sender"] for m in state["messages"]]
    assert "team" in senders and "admin" in senders


def test_waiting_count_reflects_unanswered_teams(client):
    claim_team(client, "Alpha", "1234")
    client.post("/hints", data={"body": "question one"})

    with client.application.test_client() as other:
        claim_team(other, "Beta", "5678")
        other.post("/hints", data={"body": "question two"})

    admin_login(client)
    dash = client.get("/admin/")
    assert b"2 teams waiting" in dash.data

    client.post("/admin/hints/1", data={"body": "answered"})
    dash2 = client.get("/admin/")
    assert b"1 team waiting" in dash2.data


def test_admin_hint_routes_require_admin(client):
    claim_team(client, "Alpha", "1234")
    resp = client.get("/admin/hints", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_removing_a_team_also_removes_its_messages(client):
    claim_team(client, "Alpha", "1234")
    client.post("/hints", data={"body": "will be deleted"})

    admin_login(client)
    resp = client.post("/admin/remove-team/1", follow_redirects=True)
    assert resp.status_code == 200  # no FK-constraint 500

    inbox = client.get("/admin/hints")
    assert b"will be deleted" not in inbox.data


def test_reset_wipes_messages_too(client):
    claim_team(client, "Alpha", "1234")
    client.post("/hints", data={"body": "gone after reset"})

    admin_login(client)
    resp = client.post("/admin/reset", follow_redirects=True)
    assert resp.status_code == 200  # no FK-constraint 500

    inbox = client.get("/admin/hints")
    assert b"gone after reset" not in inbox.data
    assert b"No teams have asked anything yet" in inbox.data
