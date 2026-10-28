from conftest import admin_login, claim_team


def test_admin_is_gated_from_setting_vm_ip(client):
    resp = client.post("/admin/vm-ip", data={"vm_ip": "10.0.0.5"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_submit_page_shows_placeholder_when_vm_ip_not_set(client):
    resp = claim_team(client, "Alpha", "1234")
    assert b"hasn&#39;t shared the lab address" in resp.data or b"hasn't shared the lab address" in resp.data
    assert b"vm-ip-countdown" not in resp.data


def test_first_visit_after_admin_sets_it_shows_the_countdown(app, client):
    # claim_team() follows the post-claim redirect straight to /submit,
    # so its own response IS the team's first view of that page.
    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/vm-ip", data={"vm_ip": "203.0.113.5:8080"})

    resp = claim_team(client, "Alpha", "1234")
    assert b'id="vm-ip-countdown"' in resp.data
    assert b"203.0.113.5:8080" in resp.data


def test_second_visit_shows_the_value_directly_without_a_countdown(app, client):
    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/vm-ip", data={"vm_ip": "203.0.113.5:8080"})

    claim_team(client, "Alpha", "1234")  # first visit, via the redirect follow
    resp = client.get("/submit")  # second visit -- should be plain now
    assert b'id="vm-ip-countdown"' not in resp.data
    assert b'class="vm-ip-value"' in resp.data
    assert b"203.0.113.5:8080" in resp.data


def test_updating_the_ip_shows_the_countdown_again(app, client):
    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/vm-ip", data={"vm_ip": "203.0.113.5:8080"})

    claim_team(client, "Alpha", "1234")  # sees the first address

    admin.post("/admin/vm-ip", data={"vm_ip": "203.0.113.9:8080"})
    resp = client.get("/submit")  # a new address -- countdown again
    assert b'id="vm-ip-countdown"' in resp.data
    assert b"203.0.113.9:8080" in resp.data


def test_a_different_team_gets_its_own_independent_countdown(app):
    admin = app.test_client()
    admin_login(admin)
    admin.post("/admin/vm-ip", data={"vm_ip": "203.0.113.5:8080"})

    alpha = app.test_client()
    bravo = app.test_client()

    claim_team(alpha, "Alpha", "1234")  # Alpha's first (and only, here) visit
    resp_bravo = claim_team(bravo, "Bravo", "1234")  # Bravo's own first visit
    assert b'id="vm-ip-countdown"' in resp_bravo.data

    resp_alpha_again = alpha.get("/submit")
    assert b'id="vm-ip-countdown"' not in resp_alpha_again.data
