"""The Forgotten Administrator — vulnerable Flask application.

This app is deliberately insecure. It exists only to teach IDOR and
credential-reuse in an isolated CTF lab. Do not deploy it anywhere else.

Two application identities are seeded: "john" (normal user) and "admin"
(application admin). These are web-app identities only — they are NOT
automatically the same thing as the Linux OS accounts "john"/"admin"/
"root" created in the VM (Phase 3). The story deliberately blurs them:
the admin account's web password IS also set as the Linux admin
account's real SSH password (see vm/scripts/remote-provision.sh) — on
purpose, as the intended Stage 4 lesson (password reuse across trust
boundaries), not by coincidence.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from flask import Flask

from . import db as db_module


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    # Dev default: the repo's own challenge-data/ (player-safe content
    # only -- stage1-osint, stage2-metadata, stage3 archive, tools).
    # On the VM this is overridden to a curated copy at
    # /opt/forgotten-admin/public-data (see vm/scripts/remote-provision.sh)
    # -- never point this at instructor-material/ or app source.
    default_public_data_dir = (
        Path(__file__).resolve().parent.parent.parent / "challenge-data"
    )
    app.config.from_mapping(
        SECRET_KEY="dev-only-secret-not-for-the-real-lab",
        DATABASE=os.path.join(app.instance_path, "forgotten_admin.sqlite3"),
        PUBLIC_DATA_DIR=str(default_public_data_dir),
    )
    if config:
        app.config.from_mapping(config)

    os.makedirs(app.instance_path, exist_ok=True)

    db_module.init_app(app)

    from . import auth, records, materials

    app.register_blueprint(auth.bp)
    app.register_blueprint(records.bp)
    app.register_blueprint(materials.bp)

    @app.route("/")
    def index():
        from flask import render_template

        # Public landing page (Section 6: "a player-facing starting
        # point that does not immediately reveal the genuine flag") --
        # not a login redirect, so players arriving with no credentials
        # at all still have somewhere to start.
        return render_template("landing.html")

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.route("/robots.txt")
    def robots_txt():
        from flask import Response

        # Pure flavor, not a hint: every path below is fictional or
        # already a dead end elsewhere (/admin/diagnostics is teased in
        # the admin handover record but was never actually built; the
        # "forbidden" OSINT page just leads to the employee directory's
        # own joke). None of this disallows anything that matters.
        body = (
            "User-agent: *\n"
            "Disallow: /admin/diagnostics/\n"
            "Disallow: /backup-2019/\n"
            "Disallow: /old-site/\n"
            "Disallow: /internal-tools/\n"
            "Disallow: /materials/osint/lol.html\n"
        )
        return Response(body, mimetype="text/plain")

    return app
