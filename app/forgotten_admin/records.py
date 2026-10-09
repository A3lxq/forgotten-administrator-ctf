"""Record viewing — contains the intentional IDOR (Section 9).

GET /records/<id> only checks that *someone* is logged in. It does not
check that the logged-in user owns that record id. That omission is the
entire vulnerability: a normal user (john) can read another user's
(admin's) record simply by changing the id in the URL.
"""
from __future__ import annotations

from flask import Blueprint, abort, g, redirect, render_template, url_for

from .auth import login_required
from .db import get_db

bp = Blueprint("records", __name__, url_prefix="/records")


@bp.route("/mine")
@login_required
def my_record():
    db = get_db()
    row = db.execute(
        "SELECT id FROM records WHERE owner_user_id = ? ORDER BY id LIMIT 1",
        (g.user["id"],),
    ).fetchone()
    if row is None:
        abort(404)
    return redirect(url_for("records.view_record", record_id=row["id"]))


@bp.route("/<int:record_id>")
@login_required
def view_record(record_id: int):
    db = get_db()
    # --- INTENTIONAL VULNERABILITY (IDOR) ---
    # A correct implementation would also require:
    #     AND owner_user_id = ?  (with g.user["id"])
    # or an equivalent authorization check. It is deliberately absent so
    # any logged-in user can view any record by id.
    record = db.execute(
        "SELECT r.id, r.title, r.body, u.username AS owner "
        "FROM records r JOIN users u ON u.id = r.owner_user_id "
        "WHERE r.id = ?",
        (record_id,),
    ).fetchone()
    if record is None:
        abort(404)
    return render_template("record.html", record=record)
