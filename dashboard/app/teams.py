"""Team claim/resume and flag submission.

A team "claims" a name by picking one plus a short PIN the first time they
submit -- no pre-registration, no email, nothing beyond enough friction to
stop another team casually submitting under someone else's name. The PIN
is hashed (Werkzeug, same as the main CTF app's own passwords), never
stored or logged in plaintext.
"""
from __future__ import annotations

import functools

from flask import Blueprint, current_app, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("teams", __name__)

MIN_PIN_LENGTH = 4


@bp.before_app_request
def load_current_team():
    team_id = session.get("team_id")
    if team_id is None:
        g.team = None
    else:
        g.team = get_db().execute(
            "SELECT id, name FROM teams WHERE id = ?", (team_id,)
        ).fetchone()


def team_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.team is None:
            return redirect(url_for("teams.claim"))
        return view(**kwargs)

    return wrapped


@bp.route("/", methods=("GET", "POST"))
def claim():
    """Claim a new team name, or resume an existing one -- same form,
    same logic either way: if the name exists, the PIN must match; if
    it doesn't, this creates it."""
    error = None
    if request.method == "POST":
        name = request.form.get("team_name", "").strip()
        pin = request.form.get("pin", "")

        if not name:
            error = "Team name can't be empty."
        elif len(pin) < MIN_PIN_LENGTH:
            error = f"PIN must be at least {MIN_PIN_LENGTH} characters."
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id, pin_hash FROM teams WHERE name = ?", (name,)
            ).fetchone()
            if existing is None:
                cur = db.execute(
                    "INSERT INTO teams (name, pin_hash) VALUES (?, ?)",
                    (name, generate_password_hash(pin)),
                )
                db.commit()
                team_id = cur.lastrowid
            elif check_password_hash(existing["pin_hash"], pin):
                team_id = existing["id"]
            else:
                error = "That team name is taken and this PIN doesn't match it."
                team_id = None

            if error is None:
                session.clear()
                session["team_id"] = team_id
                return redirect(url_for("teams.submit"))

    return render_template("claim.html", error=error)


@bp.route("/submit", methods=("GET", "POST"))
@team_required
def submit():
    result = None
    if request.method == "POST":
        flag_value = request.form.get("flag_value", "").strip()
        result = _handle_submission(flag_value)

    db = get_db()
    history = db.execute(
        "SELECT flag_value, classification, points_awarded, submitted_at "
        "FROM submissions WHERE team_id = ? ORDER BY submitted_at DESC",
        (g.team["id"],),
    ).fetchall()
    score = sum(row["points_awarded"] for row in history)
    genuine_found = sum(1 for row in history if row["classification"] == "genuine")

    return render_template(
        "submit.html",
        result=result,
        history=history,
        score=score,
        genuine_found=genuine_found,
        genuine_total=current_app.flag_book.genuine_count,
    )


def _handle_submission(flag_value: str) -> dict:
    if not flag_value:
        return {"status": "empty", "message": "Enter a flag value first."}

    db = get_db()
    event = db.execute("SELECT ended_at FROM event_state WHERE id = 1").fetchone()
    if event is not None and event["ended_at"] is not None:
        return {
            "status": "event_ended",
            "message": "The event has ended -- submissions are no longer being scored.",
        }

    already = db.execute(
        "SELECT classification, points_awarded FROM submissions "
        "WHERE team_id = ? AND flag_value = ?",
        (g.team["id"], flag_value),
    ).fetchone()
    if already is not None:
        return {
            "status": "duplicate",
            "message": f"Your team already submitted this one "
            f"({already['classification']}, {already['points_awarded']} pts).",
        }

    classification = current_app.flag_book.classify(flag_value)
    if classification["classification"] == "invalid":
        return {"status": "invalid", "message": "Not a recognized flag."}

    db.execute(
        "INSERT INTO submissions "
        "(team_id, flag_value, classification, flag_id, points_awarded) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            g.team["id"],
            flag_value,
            classification["classification"],
            classification["id"],
            classification["points"],
        ),
    )
    db.commit()

    from .leaderboard import check_and_set_live_winner

    check_and_set_live_winner(db, current_app.flag_book.genuine_count)

    if classification["classification"] == "genuine":
        return {
            "status": "genuine",
            "message": f"Correct! +{classification['points']} points.",
        }
    return {
        "status": "decoy",
        "message": "That's a decoy -- a real thing to find, but it "
        "doesn't score. Keep looking.",
    }


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("teams.claim"))
