"""Serves the Stage 1-3 player materials (OSINT pages, metadata photos,
the Stage 3 git-history archive, and the flagcrypto.py tool) directly
from the running app, so importing the VM is the only setup step a
player needs -- no separately-handed-out folder required.

Everything here is intentionally UNAUTHENTICATED (Section 6: "a
player-facing starting point") and read-only. `send_from_directory` is
used throughout specifically because it validates the requested path
stays inside the given directory (rejects `..` traversal) -- this is
not the app's intentional vulnerability surface, so it must not become
an accidental one.

PUBLIC_DATA_DIR must point ONLY at player-safe content (challenge-data/
in dev; a curated copy on the VM -- see vm/scripts/remote-provision.sh).
It must never be pointed at instructor-material/ or the flag manifest.
"""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, send_from_directory

bp = Blueprint("materials", __name__, url_prefix="/materials")


def _data_dir() -> Path:
    return Path(current_app.config["PUBLIC_DATA_DIR"])


@bp.route("/")
def index():
    return render_template("materials_index.html")


@bp.route("/osint/<path:filename>")
def osint_file(filename: str):
    d = _data_dir() / "stage1-osint"
    if not d.is_dir():
        abort(404)
    return send_from_directory(d, filename)


@bp.route("/metadata/<path:filename>")
def metadata_file(filename: str):
    d = _data_dir() / "stage2-metadata"
    if not d.is_dir():
        abort(404)
    return send_from_directory(d, filename)


@bp.route("/stage3-git-history.tar.gz")
def stage3_archive():
    d = _data_dir()
    if not (d / "stage3-git-history.tar.gz").is_file():
        abort(404)
    return send_from_directory(d, "stage3-git-history.tar.gz")


@bp.route("/tools/flagcrypto.py")
def flagcrypto_tool():
    d = _data_dir() / "tools"
    if not d.is_dir():
        abort(404)
    return send_from_directory(d, "flagcrypto.py")
