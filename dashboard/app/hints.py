"""Team-facing hint requests -- a message thread between one team and
the admin. Strictly one-to-one: a team can only ever read or post to
its OWN thread (every query here is scoped to g.team["id"], which
comes from the signed server-side session set at team claim/resume --
never from a URL or form field), and there is no route anywhere, team-
or admin-facing, that lets one team see another team's messages or
contact another team directly. See admin.py for the admin side.
"""
from __future__ import annotations

from flask import Blueprint, g, jsonify, redirect, render_template, request, url_for

from .db import get_db
from .teams import team_required

bp = Blueprint("hints", __name__)

MAX_MESSAGE_LENGTH = 2000


@bp.route("/hints", methods=("GET", "POST"))
@team_required
def thread():
    db = get_db()
    error = None

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if not body:
            error = "Type a question first."
        elif len(body) > MAX_MESSAGE_LENGTH:
            error = f"Keep it under {MAX_MESSAGE_LENGTH} characters."
        else:
            db.execute(
                "INSERT INTO messages (team_id, sender, body) VALUES (?, 'team', ?)",
                (g.team["id"], body),
            )
            db.commit()
            return redirect(url_for("hints.thread"))

    messages = db.execute(
        "SELECT sender, body, sent_at FROM messages "
        "WHERE team_id = ? ORDER BY sent_at ASC",
        (g.team["id"],),
    ).fetchall()

    # Visiting the page itself is what marks the thread "read" -- the
    # polled /hints/unread endpoint below only ever reports, never marks.
    db.execute(
        "UPDATE teams SET hints_last_read_at = strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime') WHERE id = ?",
        (g.team["id"],),
    )
    db.commit()

    return render_template("hints.html", messages=messages, error=error)


@bp.route("/hints/state")
@team_required
def state():
    """Polled by hints.html so a team sees an admin reply live, the
    same pattern as the leaderboard's /leaderboard/state. Scoped to
    g.team["id"] exactly like the page route above -- same isolation
    guarantee applies here."""
    db = get_db()
    messages = db.execute(
        "SELECT sender, body, sent_at FROM messages "
        "WHERE team_id = ? ORDER BY sent_at ASC",
        (g.team["id"],),
    ).fetchall()
    # A team polling /hints/state with the page already open is
    # implicitly "reading" new replies as they arrive too -- keep
    # hints_last_read_at current so the nav badge (polled from every
    # other page) doesn't also claim there's something unread here.
    db.execute(
        "UPDATE teams SET hints_last_read_at = strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime') WHERE id = ?",
        (g.team["id"],),
    )
    db.commit()
    return jsonify(
        {
            "messages": [
                {"sender": m["sender"], "body": m["body"], "sent_at": m["sent_at"]}
                for m in messages
            ]
        }
    )


@bp.route("/hints/unread")
@team_required
def unread():
    """Polled from the shared nav (every team-facing page) so a team
    notices an admin reply even while browsing the leaderboard/rules/
    submit pages, not just while /hints itself is open."""
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) AS n FROM messages
        WHERE team_id = ? AND sender = 'admin'
          AND sent_at > COALESCE(
              (SELECT hints_last_read_at FROM teams WHERE id = ?), ''
          )
        """,
        (g.team["id"], g.team["id"]),
    ).fetchone()
    return jsonify({"unread": row["n"] > 0})
