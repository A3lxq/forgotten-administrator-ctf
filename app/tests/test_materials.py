"""Proves the player materials (Stage 1-3 content) are served directly
by the app, unauthenticated, and that path traversal can't reach
anything outside the designated player-safe directory (Section 6: a
public starting point; must never expose app source or
instructor-material).
"""


def test_landing_page_is_public_and_links_to_materials(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"materials" in resp.data.lower()


def test_materials_index_is_public(client):
    resp = client.get("/materials/")
    assert resp.status_code == 200
    assert b"OSINT" in resp.data


def test_osint_profile_is_public_and_contains_flag1(client):
    resp = client.get("/materials/osint/profile.html")
    assert resp.status_code == 200
    assert b"jtyler_dev" in resp.data


def test_osint_project_page_contains_build_fingerprint(client):
    resp = client.get("/materials/osint/project-page.html")
    assert resp.status_code == 200
    assert b"SYN{" in resp.data  # the genuine flag is meant to be here


def test_metadata_photo_is_downloadable(client):
    resp = client.get("/materials/metadata/handover_photo.png")
    assert resp.status_code == 200
    assert resp.data[:8] == b"\x89PNG\r\n\x1a\n"  # real PNG magic bytes


def test_stage3_archive_is_downloadable(client):
    resp = client.get("/materials/stage3-git-history.tar.gz")
    assert resp.status_code == 200
    assert resp.data[:2] == b"\x1f\x8b"  # gzip magic bytes
    assert len(resp.data) > 1000


def test_flagcrypto_tool_is_downloadable(client):
    resp = client.get("/materials/tools/flagcrypto.py")
    assert resp.status_code == 200
    assert b"AESGCM" in resp.data


def test_path_traversal_is_rejected(client):
    for path in (
        "/materials/osint/../../app/forgotten_admin/db.py",
        "/materials/osint/..%2f..%2fapp/forgotten_admin/db.py",
        "/materials/metadata/../../../instructor-material/flag-manifest.json",
    ):
        resp = client.get(path)
        assert resp.status_code in (400, 404), f"{path} returned {resp.status_code}"


def test_nonexistent_material_404s(client):
    resp = client.get("/materials/osint/does-not-exist.html")
    assert resp.status_code == 404


def test_employee_directory_is_public_and_links_to_real_profile(client):
    resp = client.get("/materials/osint/directory.html")
    assert resp.status_code == 200
    assert b'href="profile.html"' in resp.data  # the one real link in the list


def test_fake_employees_all_land_on_the_same_joke_page(client):
    resp = client.get("/materials/osint/lol.html")
    assert resp.status_code == 200
    assert b"LOL" in resp.data


def test_robots_txt_is_public_and_fictional(client):
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert resp.mimetype == "text/plain"
    # None of these should be real routes -- confirms the bait paths
    # don't accidentally disallow anything that actually matters.
    for path in (b"/admin/diagnostics/", b"/backup-2019/", b"/old-site/", b"/internal-tools/"):
        assert path in resp.data
    for real_path in (b"Disallow: /materials/osint/profile.html", b"Disallow: /materials/osint/project-page.html",
                       b"Disallow: /materials/\n", b"/records/", b"/login"):
        assert real_path not in resp.data
