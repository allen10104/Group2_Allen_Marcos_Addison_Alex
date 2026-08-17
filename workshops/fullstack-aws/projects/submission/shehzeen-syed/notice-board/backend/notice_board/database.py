"""
PostgreSQL connection handling and schema bootstrap.

Each request opens and closes its own connection rather than pooling,
since this runs inside a Lambda invocation rather than a long-lived
server process that could keep a pool warm between requests.

PG_HOST/PG_DB/PG_USER/PG_PASSWORD are read lazily (inside get_connection,
not at import time) so a missing value only breaks requests that touch
the database, not the whole app's cold start.
"""

import os

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", "5432"),
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        connect_timeout=5,
    )


def ensure_tables(conn):
    """Create tables on first use, and migrate in columns added after launch."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        # Migrate users tables created before email existed.
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                author TEXT,
                pinned BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ
            )
            """
        )
        # Migrate notices tables created before pinned/updated_at existed.
        cur.execute("ALTER TABLE notices ADD COLUMN IF NOT EXISTS pinned BOOLEAN NOT NULL DEFAULT FALSE")
        cur.execute("ALTER TABLE notices ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
    conn.commit()
