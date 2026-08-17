"""
db.py — Postgres connection helper.

Reads PG_* from the environment (loaded from backend/.env via python-dotenv,
either your own local file for dev, or the one written by Terraform's
user_data on the EC2 instance in production).
"""
import os
from pathlib import Path

from dotenv import load_dotenv
import pg8000.native

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = int(os.environ.get("PG_PORT", 5432))
PG_DATABASE = os.environ.get("PG_DATABASE", "noticeboard")
PG_USER = os.environ.get("PG_USER", "noticeboard_app")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "localdev")

_TABLE_READY = False


def get_connection():
    return pg8000.native.Connection(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
        timeout=5,
    )


def ensure_table():
    """Create the notices table if it doesn't exist yet. Safe to call repeatedly."""
    global _TABLE_READY
    if _TABLE_READY:
        return
    conn = get_connection()
    try:
        conn.run("""
            CREATE TABLE IF NOT EXISTS notices (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        # Idempotent — also upgrades a table created by an earlier version of
        # this app (pre-image/expiry) without needing a real migration tool.
        conn.run("ALTER TABLE notices ADD COLUMN IF NOT EXISTS image_key TEXT")
        conn.run("ALTER TABLE notices ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ")
    finally:
        conn.close()
    _TABLE_READY = True
