"""The Forgotten Administrator -- scoring dashboard.

A completely separate Flask application from the vulnerable CTF target
(app/forgotten_admin/). Runs on the instructor's own host machine, not on
the CTF VM, so that compromising the CTF box (which is the entire point of
the exercise) gives a team zero access to scoring data or other teams'
submissions. See instructor-material/dashboard-guide.md.
"""
from __future__ import annotations

import datetime
import os
import secrets
from pathlib import Path

from flask import Flask

from . import db as db_module
from .flags import FlagBook

# Keeps a team logged in across a dashboard restart (e.g. a power
# outage) as long as DASHBOARD_SECRET_KEY is set, and across their own
# browser being closed/reopened for this long -- a session cookie is
# otherwise cleared when the browser itself closes, regardless of the
# server's key. Generous on purpose: a long workshop day plus margin,
# not just the 2-hour event window itself.
PERMANENT_SESSION_LIFETIME = datetime.timedelta(hours=12)


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
    secret_key_is_stable = bool(secret_key)
    if not secret_key:
        # A random-per-process fallback is still strictly safer than a
        # predictable default (this key also gates /admin sessions),
        # but it means EVERY team gets logged out if the process ever
        # restarts -- set DASHBOARD_SECRET_KEY for a real event so a
        # crash/power outage doesn't cost everyone their login.
        secret_key = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        PERMANENT_SESSION_LIFETIME=PERMANENT_SESSION_LIFETIME,
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
    if not secret_key_is_stable:
        app.logger.warning(
            "DASHBOARD_SECRET_KEY is not set -- using a random key for "
            "this process only. If the dashboard restarts for any reason "
            "(crash, power outage), every team's login session is "
            "invalidated (their scores are safe either way -- only the "
            "login itself is affected). Set it before a real event: "
            "export DASHBOARD_SECRET_KEY='...'"
        )

    from . import teams, leaderboard, admin as admin_module, rules, hints

    app.register_blueprint(teams.bp)
    app.register_blueprint(leaderboard.bp)
    app.register_blueprint(admin_module.bp)
    app.register_blueprint(rules.bp)
    app.register_blueprint(hints.bp)

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
