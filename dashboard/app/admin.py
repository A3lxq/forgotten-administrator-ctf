"""Passcode-gated instructor controls.

If DASHBOARD_ADMIN_PASSCODE isn't set in the environment, every route
here 404s -- there is no default/fallback passcode shipped, matching this
project's existing rule that instructor-only material never has a
guessable or committed credential.
"""
from __future__ import annotations

import functools

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session, url_for

from .db import get_db, init_db, reset_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _passcode_configured() -> bool:
    return bool(current_app.config.get("ADMIN_PASSCODE"))


def admin_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if not _passcode_configured():
            abort(404)
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return view(**kwargs)

    return wrapped


@bp.route("/login", methods=("GET", "POST"))
def login():
    if not _passcode_configured():
        abort(404)
    error = None
    if request.method == "POST":
        passcode = request.form.get("passcode", "")
        if passcode and passcode == current_app.config["ADMIN_PASSCODE"]:
            session["is_admin"] = True
            return redirect(url_for("admin.dashboard"))
        error = "Wrong passcode."
    return render_template("admin_login.html", error=error)


@bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


def _final_winner_with_tiebreak(db) -> int | None:
    """Among teams tied for the highest score, the one that reached that
    score first wins -- computed from a running cumulative total per
    team ordered by submission time, not just the last genuine flag's
    timestamp (decoys and differing point values make that insufficient)."""
    teams = db.execute("SELECT id FROM teams").fetchall()
    if not teams:
        return None

    best_team_id = None
    best_score = -1
    best_reached_at = None

    for t in teams:
        subs = db.execute(
            "SELECT points_awarded, submitted_at FROM submissions "
            "WHERE team_id = ? ORDER BY submitted_at ASC",
            (t["id"],),
        ).fetchall()
        running = 0
        reached_at = None
        for s in subs:
            running += s["points_awarded"]
            if s["points_awarded"] > 0:
                reached_at = s["submitted_at"]
        final_score = running

        if final_score > best_score:
            best_score, best_team_id, best_reached_at = final_score, t["id"], reached_at
        elif final_score == best_score and reached_at and best_reached_at and reached_at < best_reached_at:
            best_team_id, best_reached_at = t["id"], reached_at

    return best_team_id


def _teams_waiting_for_reply(db) -> int:
    """A team is 'waiting' if its most recent message is from the team
    itself (nobody from admin has answered it yet). Ties on sent_at
    (SQLite's datetime('now') only has 1-second resolution, so a
    question and a fast reply can land in the same second) are broken
    by id, which is strictly insertion-ordered -- without this, two
    same-second rows have no reliable "most recent" and ROW_NUMBER()'s
    tie order is unspecified."""
    row = db.execute(
        """
        SELECT COUNT(*) AS n FROM (
            SELECT team_id, sender,
                   ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY sent_at DESC, id DESC) AS rn
            FROM messages
        )
        WHERE rn = 1 AND sender = 'team'
        """
    ).fetchone()
    return row["n"]


@bp.route("/")
@admin_required
def dashboard():
    db = get_db()
    teams = db.execute(
        """
        SELECT t.id, t.name, t.created_at,
               COALESCE(SUM(s.points_awarded), 0) AS score,
               COUNT(s.id) AS submission_count
        FROM teams t
        LEFT JOIN submissions s ON s.team_id = t.id
        GROUP BY t.id
        ORDER BY score DESC, t.name ASC
        """
    ).fetchall()
    event = db.execute("SELECT * FROM event_state WHERE id = 1").fetchone()
    return render_template(
        "admin.html",
        teams=teams,
        event=event,
        genuine_total=current_app.flag_book.genuine_count,
        waiting_count=_teams_waiting_for_reply(db),
    )


@bp.route("/end-event", methods=("POST",))
@admin_required
def end_event():
    db = get_db()
    winner_id = _final_winner_with_tiebreak(db)
    db.execute(
        "UPDATE event_state SET ended_at = datetime('now'), final_winner_team_id = ? "
        "WHERE id = 1",
        (winner_id,),
    )
    db.commit()
    return redirect(url_for("admin.dashboard"))


@bp.route("/reload-manifest", methods=("POST",))
@admin_required
def reload_manifest():
    current_app.flag_book.load()
    return redirect(url_for("admin.dashboard"))


@bp.route("/reset", methods=("POST",))
@admin_required
def reset():
    db = get_db()
    init_db(db)
    reset_db(db)
    return redirect(url_for("admin.dashboard"))


@bp.route("/remove-team/<int:team_id>", methods=("POST",))
@admin_required
def remove_team(team_id: int):
    db = get_db()
    db.execute("DELETE FROM messages WHERE team_id = ?", (team_id,))
    db.execute("DELETE FROM submissions WHERE team_id = ?", (team_id,))
    db.execute("DELETE FROM teams WHERE id = ?", (team_id,))
    db.execute(
        "UPDATE event_state SET live_winner_team_id = NULL WHERE live_winner_team_id = ?",
        (team_id,),
    )
    db.commit()
    return redirect(url_for("admin.dashboard"))


@bp.route("/hints")
@admin_required
def hints_inbox():
    db = get_db()
    # "Last message" subqueries all break sent_at ties by id -- SQLite's
    # datetime('now') only has 1-second resolution, so two messages for
    # the same team can land in the same second with no other reliable
    # ordering (same issue as _teams_waiting_for_reply above).
    rows = db.execute(
        """
        SELECT t.id, t.name,
               (SELECT body FROM messages m WHERE m.team_id = t.id
                ORDER BY m.sent_at DESC, m.id DESC LIMIT 1) AS last_body,
               (SELECT sender FROM messages m WHERE m.team_id = t.id
                ORDER BY m.sent_at DESC, m.id DESC LIMIT 1) AS last_sender,
               (SELECT sent_at FROM messages m WHERE m.team_id = t.id
                ORDER BY m.sent_at DESC, m.id DESC LIMIT 1) AS last_sent_at,
               (SELECT COUNT(*) FROM messages m WHERE m.team_id = t.id) AS message_count
        FROM teams t
        ORDER BY (last_sender = 'team') DESC, last_sent_at DESC
        """
    ).fetchall()
    # Teams with zero messages: last_sent_at is NULL, sorts them to the
    # bottom regardless of name -- fine, they have nothing to show yet.
    threads = [r for r in rows if r["message_count"] > 0]
    return render_template("admin_hints.html", threads=threads)


@bp.route("/hints/<int:team_id>", methods=("GET", "POST"))
@admin_required
def hint_thread(team_id: int):
    db = get_db()
    team = db.execute("SELECT id, name FROM teams WHERE id = ?", (team_id,)).fetchone()
    if team is None:
        abort(404)

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            db.execute(
                "INSERT INTO messages (team_id, sender, body) VALUES (?, 'admin', ?)",
                (team_id, body),
            )
            db.commit()
        return redirect(url_for("admin.hint_thread", team_id=team_id))

    messages = db.execute(
        "SELECT sender, body, sent_at FROM messages "
        "WHERE team_id = ? ORDER BY sent_at ASC",
        (team_id,),
    ).fetchall()
    return render_template("admin_hint_thread.html", team=team, messages=messages)


@bp.route("/hints/state")
@admin_required
def hints_state():
    """Polled from the admin dashboard/inbox so a new hint request
    shows up live without a manual refresh."""
    db = get_db()
    return jsonify({"waiting_count": _teams_waiting_for_reply(db)})
