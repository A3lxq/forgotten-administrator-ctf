"""Proves the intentional OS command injection in the admin diagnostics
tool (Section 10 requirement), and that it's gated behind the admin role.

The injection proof is deliberately non-destructive: it just creates a
marker file inside pytest's own tmp_path, which is deleted automatically
after the test. No network listener, no real reverse shell is opened
here — that end-to-end exploitation path is exercised manually against
the isolated VM in Phase 3+, per the project's safety rules.
"""
from conftest import login


def test_diagnostics_requires_admin_role(client):
    login(client, "john", "Summer2019!")
    resp = client.get("/admin/diagnostics")
    assert resp.status_code == 403


def test_diagnostics_redirects_anonymous_to_login(client):
    resp = client.get("/admin/diagnostics", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_admin_can_reach_diagnostics(client):
    login(client, "admin", "N3tOps-Diag#7")
    resp = client.get("/admin/diagnostics")
    assert resp.status_code == 200
    assert b"Network Diagnostics" in resp.data


def test_diagnostics_command_injection(client, tmp_path):
    login(client, "admin", "N3tOps-Diag#7")
    marker = tmp_path / "pwned_marker"
    assert not marker.exists()

    payload = f"127.0.0.1; touch {marker}"
    resp = client.post("/admin/diagnostics", data={"host": payload})

    assert resp.status_code == 200
    # If the app only ever ran a safe, non-shell `ping` invocation, the
    # injected `touch` would never execute and this file would not exist.
    assert marker.exists(), (
        "Command injection did not execute — the intentional "
        "vulnerability may have been accidentally fixed."
    )
