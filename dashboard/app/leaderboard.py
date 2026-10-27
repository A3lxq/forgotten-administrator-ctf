"""Public leaderboard page + the JSON state endpoint it polls.

Never exposes flag values, which flags a team is still missing, or any
other team's submission contents -- only name, score, and genuine-flag
progress count. Winner detection (live + final) lives here since it's
driven by the same score/progress data the leaderboard already computes.
"""
from __future__ import annotations

import sqlite3

from flask import Blueprint, current_app, jsonify, render_template

from .db import get_db

bp = Blueprint("leaderboard", __name__, url_prefix="/leaderboard")


def _standings(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute(
        """
        SELECT
            t.id,
            t.name,
            COALESCE(SUM(s.points_awarded), 0) AS score,
            COALESCE(SUM(CASE WHEN s.classification = 'genuine' THEN 1 ELSE 0 END), 0)
                AS genuine_found,
            MAX(CASE WHEN s.classification = 'genuine' THEN s.submitted_at END)
                AS last_genuine_at
        FROM teams t
        LEFT JOIN submissions s ON s.team_id = t.id
        GROUP BY t.id
        ORDER BY score DESC, last_genuine_at ASC NULLS LAST, t.name ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def check_and_set_live_winner(db: sqlite3.Connection, genuine_total: int) -> None:
    """Called right after a submission is recorded. If this team now
    holds every genuine flag and nobody has been marked the live winner
    yet, they are -- first past the post, not re-evaluated afterward."""
    state = db.execute("SELECT live_winner_team_id FROM event_state WHERE id = 1").fetchone()
    if state is not None and state["live_winner_team_id"] is not None:
        return  # already decided

    standings = _standings(db)
    for team in standings:
        if team["genuine_found"] >= genuine_total:
            db.execute(
                "UPDATE event_state SET live_winner_team_id = ? WHERE id = 1",
                (team["id"],),
            )
            db.commit()
            return


@bp.route("/")
def page():
    return render_template("leaderboard.html")


@bp.route("/state")
def state():
    db = get_db()
    standings = _standings(db)
    event = db.execute(
        "SELECT ended_at, live_winner_team_id, final_winner_team_id "
        "FROM event_state WHERE id = 1"
    ).fetchone()

    def team_name(team_id):
        if team_id is None:
            return None
        row = db.execute("SELECT name FROM teams WHERE id = ?", (team_id,)).fetchone()
        return row["name"] if row else None

    return jsonify(
        {
            "genuine_total": current_app.flag_book.genuine_count,
            "standings": [
                {
                    "name": t["name"],
                    "score": t["score"],
                    "genuine_found": t["genuine_found"],
                    "genuine_total": current_app.flag_book.genuine_count,
                }
                for t in standings
            ],
            "event_ended": event["ended_at"] is not None,
            "live_winner": team_name(event["live_winner_team_id"]),
            "final_winner": team_name(event["final_winner_team_id"]),
        }
    )
