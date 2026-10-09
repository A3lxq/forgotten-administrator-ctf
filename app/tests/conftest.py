import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forgotten_admin import create_app
from forgotten_admin.db import get_db, seed_db


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    app = create_app({
        "TESTING": True,
        "DATABASE": str(db_path),
    })
    with app.app_context():
        seed_db(get_db())
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password):
    return client.post(
        "/login", data={"username": username, "password": password}
    )
