"""The Forgotten Administrator -- scoring dashboard.

A completely separate Flask application from the vulnerable CTF target
(app/forgotten_admin/). Runs on the instructor's own host machine, not on
the CTF VM, so that compromising the CTF box (which is the entire point of
the exercise) gives a team zero access to scoring data or other teams'
submissions. See instructor-material/dashboard-guide.md.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask

from . import db as db_module
from .flags import FlagBook


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    # Dev default: the repo's own instructor-material/flag-manifest.json.
    default_manifest_path = (
        Path(__file__).resolve().parent.parent.parent
        / "instructor-material"
        / "flag-manifest.json"
    )

    admin_passcode = os.environ.get("DASHBOARD_ADMIN_PASSCODE")
    secret_key = os.environ.get("DASHBOARD_SECRET_KEY")
    if not secret_key:
        # A random-per-process key is fine for a single-run event (admin
        # sessions just get invalidated if the process restarts) and is
        # strictly safer than a predictable default, since this key
        # gates the "End Event"/reset admin actions.
        secret_key = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=os.path.join(app.instance_path, "dashboard.sqlite3"),
        FLAG_MANIFEST_PATH=str(default_manifest_path),
        ADMIN_PASSCODE=admin_passcode,
    )
    if config:
        app.config.from_mapping(config)

    os.makedirs(app.instance_path, exist_ok=True)

    db_module.init_app(app)

    with app.app_context():
        conn = db_module.get_db()
        db_module.init_db(conn)
        db_module.close_db()

    app.flag_book = FlagBook(Path(app.config["FLAG_MANIFEST_PATH"]))

    if not app.config["ADMIN_PASSCODE"]:
        app.logger.warning(
            "DASHBOARD_ADMIN_PASSCODE is not set -- /admin is unreachable "
            "(by design: no default passcode is shipped). Set it before "
            "a real event: export DASHBOARD_ADMIN_PASSCODE='...'"
        )

    from . import teams, leaderboard, admin as admin_module, rules

    app.register_blueprint(teams.bp)
    app.register_blueprint(leaderboard.bp)
    app.register_blueprint(admin_module.bp)
    app.register_blueprint(rules.bp)

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
