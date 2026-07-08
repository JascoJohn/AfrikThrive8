"""
Database layer — PostgreSQL (was SQLite).

Reads the connection string from the DATABASE_URL environment variable, e.g.:
    postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

Uses psycopg2 with RealDictCursor so rows behave like dictionaries
(rows["column_name"]), matching how the old sqlite3.Row-based code read them —
this keeps the rest of the app's query code almost unchanged.
"""

import os
import psycopg2
import psycopg2.extras
from flask import g

DATABASE_URL = os.environ["DATABASE_URL"]  # fails loudly if not set — see .env.example


def get_db():
    """Return a request-scoped Postgres connection (opened once per request)."""
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), fetch="all"):
    """
    Run a query with %s placeholders (Postgres style, not SQLite's ?).
    fetch: "all" | "one" | None (None = no SELECT, e.g. INSERT/UPDATE)
    Commits automatically for write statements.
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
        if fetch == "all":
            result = cur.fetchall()
        elif fetch == "one":
            result = cur.fetchone()
        else:
            result = None
    db.commit()
    return result


def init_db():
    """Create tables if they don't exist yet. Safe to call on every app start."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id TEXT PRIMARY KEY,
            session TEXT NOT NULL,
            session_label TEXT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            country TEXT,
            age_group TEXT,
            gender TEXT,
            status TEXT,
            goal TEXT,
            source TEXT,
            submitted_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS speakers (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            marital_status TEXT,
            age TEXT,
            country TEXT,
            title TEXT,
            organization TEXT,
            bio TEXT,
            headshot_path TEXT,
            email TEXT NOT NULL,
            x_handle TEXT,
            linkedin TEXT,
            topic TEXT,
            experience TEXT,
            consent INTEGER NOT NULL DEFAULT 0,
            submitted_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evaluations (
            id TEXT PRIMARY KEY,
            session TEXT NOT NULL,
            session_label TEXT,
            speaker_name TEXT NOT NULL,
            topic TEXT,
            knowledge INTEGER,
            communication INTEGER,
            engagement INTEGER,
            time_management INTEGER,
            professionalism INTEGER,
            invite_again TEXT,
            strengths TEXT,
            improve TEXT,
            evaluated_by TEXT,
            submitted_at TIMESTAMP NOT NULL
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()
