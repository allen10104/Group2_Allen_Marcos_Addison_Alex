"""
Notice board CRUD.

Reads are public. Writes require a bearer token. Editing and deleting
are scoped to a notice's own author unless the caller is an admin;
pinning a notice as "important" is admin-only.
"""

import psycopg2.extras
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import ensure_tables, get_connection
from ..schemas import NoticeCreate, NoticePinUpdate, NoticeUpdate
from ..security import get_current_user

router = APIRouter(prefix="/notices", tags=["notices"])

NOTICE_FIELDS = "id, message, author, pinned, created_at, updated_at"


def _serialize_notice(row: dict) -> dict:
    row["created_at"] = row["created_at"].isoformat()
    row["updated_at"] = row["updated_at"].isoformat() if row["updated_at"] else None
    return row


@router.get("")
def list_notices():
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Pinned ("important") notices always sort first, newest first
            # within each group — so pinning survives newer posts arriving.
            cur.execute(f"SELECT {NOTICE_FIELDS} FROM notices ORDER BY pinned DESC, created_at DESC")
            rows = cur.fetchall()
        return [_serialize_notice(row) for row in rows]
    finally:
        conn.close()


@router.post("", status_code=201)
def create_notice(body: NoticeCreate, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"INSERT INTO notices (message, author) VALUES (%s, %s) RETURNING {NOTICE_FIELDS}",
                (body.message, user["username"]),
            )
            row = cur.fetchone()
        conn.commit()
        return _serialize_notice(row)
    finally:
        conn.close()


@router.put("/{notice_id}")
def update_notice(notice_id: int, body: NoticeUpdate, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT author FROM notices WHERE id = %s", (notice_id,))
            row = cur.fetchone()

        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Notice not found")
        if row["author"] != user["username"] and not user["is_admin"]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own notices")

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"UPDATE notices SET message = %s, updated_at = now() WHERE id = %s RETURNING {NOTICE_FIELDS}",
                (body.message, notice_id),
            )
            updated = cur.fetchone()
        conn.commit()
        return _serialize_notice(updated)
    finally:
        conn.close()


@router.patch("/{notice_id}/pin")
def pin_notice(notice_id: int, body: NoticePinUpdate, user: dict = Depends(get_current_user)):
    if not user["is_admin"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can pin or unpin notices")

    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"UPDATE notices SET pinned = %s WHERE id = %s RETURNING {NOTICE_FIELDS}",
                (body.pinned, notice_id),
            )
            updated = cur.fetchone()
        if updated is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Notice not found")
        conn.commit()
        return _serialize_notice(updated)
    finally:
        conn.close()


@router.delete("/{notice_id}")
def delete_notice(notice_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT author FROM notices WHERE id = %s", (notice_id,))
            row = cur.fetchone()

        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Notice not found")
        if row["author"] != user["username"] and not user["is_admin"]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own notices")

        with conn.cursor() as cur:
            cur.execute("DELETE FROM notices WHERE id = %s", (notice_id,))
        conn.commit()
        return {"deleted": notice_id}
    finally:
        conn.close()
