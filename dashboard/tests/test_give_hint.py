from conftest import TEST_FLAGS, admin_login, claim_team

from app import hint_content


def _submit(client, flag_value):
    return client.post("/submit", data={"flag_value": flag_value}, follow_redirects=True)


def _team_messages(db, team_id):
    return db.execute(
        "SELECT sender, body FROM messages WHERE team_id = ? ORDER BY id ASC",
        (team_id,),
    ).fetchall()


def test_stage_for_progress_edge_cases():
    assert hint_content.stage_for_progress(0, 5) == 1
    assert hint_content.stage_for_progress(1, 5) == 2
    assert hint_content.stage_for_progress(4, 5) == 5
    assert hint_content.stage_for_progress(5, 5) == "completed"
    assert hint_content.stage_for_progress(99, 5) == "completed"


def test_give_hint_is_admin_gated(client):
    resp = client.post("/admin/give-hint", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_give_hint_noop_with_no_teams(app, client):
    admin_login(client)
    resp = client.post("/admin/give-hint", follow_redirects=False)
    assert resp.status_code == 302

    with app.app_context():
        from app.db import get_db

        count = get_db().execute("SELECT COUNT(*) AS n FROM messages").fetchone()["n"]
    assert count == 0


def test_give_hint_taunts_when_nobody_is_waiting(app):
    client_a = app.test_client()
    client_b = app.test_client()
    claim_team(client_a, "Alpha", "1234")
    claim_team(client_b, "Bravo", "1234")

    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/give-hint")

    with app.app_context():
        from app.db import get_db

        db = get_db()
        teams = {t["name"]: t["id"] for t in db.execute("SELECT id, name FROM teams")}
        msgs_a = _team_messages(db, teams["Alpha"])
        msgs_b = _team_messages(db, teams["Bravo"])

    assert len(msgs_a) == 1 and msgs_a[0]["sender"] == "admin"
    assert len(msgs_b) == 1 and msgs_b[0]["sender"] == "admin"
    assert msgs_a[0]["body"] in hint_content.STAGE_CONTENT[1]["taunt"]
    assert msgs_b[0]["body"] in hint_content.STAGE_CONTENT[1]["taunt"]


def test_give_hint_hints_when_half_or_more_are_waiting(app):
    client_a = app.test_client()
    client_b = app.test_client()
    claim_team(client_a, "Alpha", "1234")
    claim_team(client_b, "Bravo", "1234")

    # Exactly 50% (1 of 2) waiting -- the boundary the user confirmed
    # should count as "enough", not "not enough".
    client_a.post("/hints", data={"body": "any hints?"})

    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/give-hint")

    with app.app_context():
        from app.db import get_db

        db = get_db()
        teams = {t["name"]: t["id"] for t in db.execute("SELECT id, name FROM teams")}
        msgs_a = _team_messages(db, teams["Alpha"])
        msgs_b = _team_messages(db, teams["Bravo"])

    # Alpha's thread: their own question, then the broadcast hint.
    assert len(msgs_a) == 2
    assert msgs_a[1]["body"] in hint_content.STAGE_CONTENT[1]["hint"]
    assert len(msgs_b) == 1
    assert msgs_b[0]["body"] in hint_content.STAGE_CONTENT[1]["hint"]


def test_give_hint_is_tailored_per_team_stage(app):
    client_a = app.test_client()
    client_b = app.test_client()
    claim_team(client_a, "Alpha", "1234")
    claim_team(client_b, "Bravo", "1234")

    # Alpha found one genuine flag already (stage 2); Bravo found none
    # (stage 1). Both wait on a reply so this stays in hint mode.
    _submit(client_a, TEST_FLAGS["flags"][0]["value"])
    client_a.post("/hints", data={"body": "stuck"})
    client_b.post("/hints", data={"body": "stuck too"})

    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/give-hint")

    with app.app_context():
        from app.db import get_db

        db = get_db()
        teams = {t["name"]: t["id"] for t in db.execute("SELECT id, name FROM teams")}
        last_a = _team_messages(db, teams["Alpha"])[-1]
        last_b = _team_messages(db, teams["Bravo"])[-1]

    assert last_a["body"] in hint_content.STAGE_CONTENT[2]["hint"]
    assert last_b["body"] in hint_content.STAGE_CONTENT[1]["hint"]
    assert last_a["body"] != last_b["body"] or hint_content.STAGE_CONTENT[2]["hint"] == hint_content.STAGE_CONTENT[1]["hint"]


def test_give_hint_never_crosses_team_boundaries(app):
    client_a = app.test_client()
    client_b = app.test_client()
    claim_team(client_a, "Alpha", "1234")
    claim_team(client_b, "Bravo", "1234")

    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/give-hint")

    with app.app_context():
        from app.db import get_db

        db = get_db()
        teams = {t["name"]: t["id"] for t in db.execute("SELECT id, name FROM teams")}
        msgs_a = _team_messages(db, teams["Alpha"])
        msgs_b = _team_messages(db, teams["Bravo"])

    # Each team's thread holds exactly its own single broadcast message
    # -- nothing from the other team's thread, same guarantee the
    # existing hint-reply isolation tests already hold.
    assert len(msgs_a) == 1
    assert len(msgs_b) == 1


def test_hint_content_never_leaks_a_real_flag_format():
    for bucket in hint_content.STAGE_CONTENT.values():
        for variants in bucket.values():
            for text in variants:
                assert "SYN{" not in text
                assert "FFLAG{" not in text
