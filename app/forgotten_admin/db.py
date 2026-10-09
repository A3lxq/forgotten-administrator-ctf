"""SQLite storage for the fictional web application identities and records.

Everything here is intentionally simple (stdlib sqlite3, no ORM) — this is
a teaching lab, not a production app.
"""
from __future__ import annotations

import sqlite3

import click
from flask import Flask, current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    body TEXT NOT NULL
);
"""

# Seeded, disposable, fictional credentials for the lab only.
# The admin web password is intentionally discoverable by players through
# the IDOR vulnerability (Stage 4) — that disclosure IS the puzzle, so it
# is seeded here deliberately rather than hidden.
SEED_USERS = [
    {"username": "john", "password": "Summer2019!", "is_admin": False},
    {"username": "admin", "password": "N3tOps-Diag#7", "is_admin": True},
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def seed_db(conn: sqlite3.Connection) -> None:
    """Idempotent: safe to call on every app start without duplicating
    users or records."""
    init_db(conn)

    user_ids: dict[str, int] = {}
    for u in SEED_USERS:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (u["username"],)
        ).fetchone()
        if row is None:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) "
                "VALUES (?, ?, ?)",
                (
                    u["username"],
                    generate_password_hash(u["password"]),
                    1 if u["is_admin"] else 0,
                ),
            )
            user_ids[u["username"]] = cur.lastrowid
        else:
            user_ids[u["username"]] = row["id"]

    existing = conn.execute("SELECT COUNT(*) AS n FROM records").fetchone()["n"]
    if existing == 0:
        conn.execute(
            "INSERT INTO records (owner_user_id, title, body) VALUES (?, ?, ?)",
            (
                user_ids["john"],
                "Handover notes",
                "Reminder to self: finish migrating the internal tools "
                "before I leave. Ask admin about the diagnostics access "
                "if anything looks broken after the handover.",
            ),
        )
        # The designated administrative record (Section 9/11). It should
        # require the admin identity to view normally; the IDOR lets a
        # logged-in john read it anyway by changing the record id.
        conn.execute(
            "INSERT INTO records (owner_user_id, title, body) VALUES (?, ?, ?)",
            (
                user_ids["admin"],
                "Admin handover record (internal use only)",
                "Internal diagnostics console: /admin/diagnostics "
                "(login as this account to use it). "
                "Login for this account during the handover window: "
                "admin / N3tOps-Diag#7 — rotate after the review.",
            ),
        )
    conn.commit()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Create empty tables (for inspection); does not seed data."""
        with app.app_context():
            init_db(get_db())
        click.echo("Initialized the database schema.")

    @app.cli.command("seed")
    def seed_command():
        """Create tables (if needed) and seed users/records. Idempotent."""
        with app.app_context():
            seed_db(get_db())
        click.echo("Seeded database (idempotent).")
