"""SQLite storage for the scoring dashboard.

Completely separate database from the CTF app's own (app/forgotten_admin/
db.py) -- this process never touches, and is never reachable from, the
vulnerable VM. Same stdlib-sqlite3-no-ORM style as the rest of this
project.
"""
from __future__ import annotations

import sqlite3

import click
from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    pin_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    flag_value TEXT NOT NULL,
    classification TEXT NOT NULL,  -- genuine | decoy
    flag_id TEXT,                   -- e.g. original_flag_3, d2b
    points_awarded INTEGER NOT NULL DEFAULT 0,
    submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (team_id, flag_value)
);

CREATE TABLE IF NOT EXISTS event_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT,
    live_winner_team_id INTEGER REFERENCES teams(id),
    final_winner_team_id INTEGER REFERENCES teams(id)
);
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    # Single event_state row, created once.
    conn.execute("INSERT OR IGNORE INTO event_state (id) VALUES (1)")
    conn.commit()


def reset_db(conn: sqlite3.Connection) -> None:
    """Wipe all teams/submissions/event state for a fresh event run.
    Does not touch flag-manifest.json or anything outside this DB."""
    conn.executescript(
        "DELETE FROM submissions; DELETE FROM teams; DELETE FROM event_state;"
    )
    conn.execute("INSERT INTO event_state (id) VALUES (1)")
    conn.commit()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables (idempotent, does not wipe existing data)."""
        with app.app_context():
            init_db(get_db())
        click.echo("Initialized the dashboard database schema.")

    @app.cli.command("reset-db")
    def reset_db_command():
        """Wipe all teams/submissions/event state. Destructive."""
        with app.app_context():
            init_db(get_db())
            reset_db(get_db())
        click.echo("Dashboard database reset -- ready for a fresh event.")
