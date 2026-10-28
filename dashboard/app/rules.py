"""A static page showing player-material/Rules.md's content inside the
dashboard, so players have it visible without needing the handed-out
file open separately. The content is duplicated here deliberately
(not read from the file at request time) -- the dashboard is meant to
run standalone, including from the packaged release, which doesn't
necessarily have player-material/ alongside it. Keep this in sync with
player-material/Rules.md by hand if the rules ever change.
"""
from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("rules", __name__)


@bp.route("/rules")
def page():
    return render_template("rules.html")
