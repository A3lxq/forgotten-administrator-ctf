"""The Forgotten Administrator — vulnerable Flask application.

This app is deliberately insecure. It exists only to teach IDOR and OS
command injection in an isolated CTF lab. Do not deploy it anywhere else.

Two application identities are seeded: "john" (normal user) and "admin"
(application admin). These are web-app identities only — they are NOT the
same thing as the Linux OS accounts "john"/"admin"/"root" created in the
VM (Phase 3). The story deliberately blurs the two; the code must not.
"""
from __future__ import annotations

import os
import sqlite3

from flask import Flask

from . import db as db_module


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev-only-secret-not-for-the-real-lab",
        DATABASE=os.path.join(app.instance_path, "forgotten_admin.sqlite3"),
        # Command used by the intentionally vulnerable diagnostics feature.
        # In the real VM (Phase 3) this is invoked through a narrowly scoped
        # sudoers rule as the Linux "admin" account; here it just runs
        # locally so the vulnerability itself can be developed and tested.
        DIAG_PING_BINARY="ping",
    )
    if config:
        app.config.from_mapping(config)

    os.makedirs(app.instance_path, exist_ok=True)

    db_module.init_app(app)

    from . import auth, records, admin as admin_bp

    app.register_blueprint(auth.bp)
    app.register_blueprint(records.bp)
    app.register_blueprint(admin_bp.bp)

    @app.route("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("auth.login"))

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
