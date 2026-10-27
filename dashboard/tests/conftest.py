import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.db import get_db, init_db  # noqa: E402

# Small, self-contained test manifest -- independent of the real
# instructor-material/flag-manifest.json so these tests don't silently
# change behavior if the real flags are ever edited. Same schema shape.
TEST_FLAGS = {
    "flags": [
        {"id": "g1", "classification": "genuine", "points": 100, "value": "SYN{test_one}"},
        {"id": "g2", "classification": "genuine", "points": 150, "value": "SYN{test_two}"},
        {"id": "d1", "classification": "decoy", "points": 0, "value": "FFLAG{test_decoy}"},
    ]
}


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    manifest_path = tmp_path / "flag-manifest.json"
    manifest_path.write_text(json.dumps(TEST_FLAGS))

    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "FLAG_MANIFEST_PATH": str(manifest_path),
            "ADMIN_PASSCODE": "test-passcode",
        }
    )
    with app.app_context():
        init_db(get_db())
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def claim_team(client, name="Alpha", pin="1234"):
    return client.post("/", data={"team_name": name, "pin": pin}, follow_redirects=True)


def admin_login(client, passcode="test-passcode"):
    return client.post("/admin/login", data={"passcode": passcode}, follow_redirects=True)
