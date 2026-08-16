import os

import psycopg
from dotenv import load_dotenv

from backend.models.category import Category
from backend.models.notice import Notice

load_dotenv()


class PostgresNoticeRepository:
    """Postgres storage for notices. Same interface as InMemoryNoticeRepository."""

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is not set. Add it to a .env file "
                "(see .env.example)."
            )
        self._ensure_table()

    def _connect(self):
        return psycopg.connect(self.database_url)

    def _ensure_table(self) -> None:
        with self._connect() as conn:
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

    def next_id(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT nextval(pg_get_serial_sequence('notices', 'id'))"
            ).fetchone()
            return int(row[0])

    def list_all(self) -> list[Notice]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, date, content, category, author, author_id
                FROM notices
                ORDER BY id
                """
            ).fetchall()
        return [self._row_to_notice(row) for row in rows]

    def get(self, notice_id: int) -> Notice | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, title, date, content, category, author, author_id
                FROM notices
                WHERE id = %s
                """,
                (notice_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_notice(row)

    def add(self, notice: Notice) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO notices (id, title, date, content, category, author, author_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    notice.id,
                    notice.title,
                    str(notice.date),
                    notice.content,
                    notice.category.value,
                    notice.author,
                    notice.author_id,
                ),
            )
            conn.commit()

    def update(self, notice: Notice) -> None:
        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE notices
                SET title = %s,
                    date = %s,
                    content = %s,
                    category = %s,
                    author = %s,
                    author_id = %s
                WHERE id = %s
                """,
                (
                    notice.title,
                    str(notice.date),
                    notice.content,
                    notice.category.value,
                    notice.author,
                    notice.author_id,
                    notice.id,
                ),
            )
            if result.rowcount == 0:
                raise ValueError("Notice not found")
            conn.commit()

    def delete(self, notice_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM notices WHERE id = %s", (notice_id,))
            conn.commit()

    @staticmethod
    def _row_to_notice(row) -> Notice:
        notice_id, title, notice_date, content, category, author, author_id = row
        notice = Notice(
            id=notice_id,
            title=title,
            date=str(notice_date),
            content=content,
            category=Category(category),
        )
        notice.author = author
        notice.author_id = author_id
        return notice
