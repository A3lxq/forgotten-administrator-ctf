def test_rules_page_is_public(client):
    resp = client.get("/rules")
    assert resp.status_code == 200
    assert b"Scope" in resp.data
    assert b"No denial-of-service" in resp.data


def test_rules_page_includes_no_ai_and_no_flag_sharing(client):
    resp = client.get("/rules")
    assert b"No AI assistance" in resp.data
    assert b"No flag sharing" in resp.data


def test_rules_summary_shown_on_claim_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Before you start" in resp.data
    assert b"decoy" in resp.data.lower()


def test_claim_page_summary_includes_no_ai_and_no_flag_sharing(client):
    resp = client.get("/")
    assert b"No AI assistance" in resp.data
    assert b"No flag sharing" in resp.data
