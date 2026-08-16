"""
Quick Postgres / Supabase connection check.

Run from the Group2 project folder (venv active):
    python test_db_connection.py
"""

from dotenv import load_dotenv
import os
import sys

load_dotenv()


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("FAIL: DATABASE_URL is not set in the environment or .env")
        return 1

    # Never print the full URL (it contains the password). Show a redacted hint.
    if "@" in database_url:
        scheme_and_user, host_part = database_url.split("@", 1)
        user = scheme_and_user.split("://", 1)[-1].split(":", 1)[0]
        print(f"Connecting as user={user!r} to host part: ...@{host_part}")
    else:
        print("Connecting with DATABASE_URL (format looks unusual — expected user@host)")

    try:
        import psycopg
    except ImportError:
        print("FAIL: psycopg is not installed. Run: pip install 'psycopg[binary]'")
        return 1

    try:
        with psycopg.connect(database_url, connect_timeout=10) as conn:
            row = conn.execute("SELECT version(), current_database(), current_user").fetchone()
            print("OK: connected")
            print(f"  database: {row[1]}")
            print(f"  user:     {row[2]}")
            print(f"  version:  {row[0].split(',')[0]}")

            # Same table the repository creates
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notices (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    author TEXT,
                    author_id INTEGER
                )
                """
            )
            conn.commit()
            count = conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
            print(f"OK: notices table ready ({count} row(s))")
        return 0
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
