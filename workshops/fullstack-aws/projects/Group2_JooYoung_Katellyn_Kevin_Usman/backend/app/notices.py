from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .db import ensure_table, get_connection

router = APIRouter()

EXPIRY_DURATIONS: dict[str, Optional[timedelta]] = {
    "never": None,
    "1d": timedelta(days=1),
    "3d": timedelta(days=3),
    "1w": timedelta(weeks=1),
}


class NoticeCreate(BaseModel):
    name: str
    message: str
    image_key: Optional[str] = None
    expires_in: str = "never"


def row_to_notice(row):
    id_, name, message, image_key, expires_at, created_at = row
    return {
        "id": str(id_),
        "name": name,
        "message": message,
        # Relative path: resolves against whatever origin served the page.
        # In production that's the CloudFront domain (frontend + /uploads/*
        # both live behind it), so no separate "public base URL" is needed.
        "image_url": f"/uploads/{image_key}" if image_key else None,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "created_at": created_at.isoformat() if created_at else None,
    }


@router.get("/notices")
def list_notices():
    ensure_table()
    conn = get_connection()
    try:
        rows = conn.run(
            """
            SELECT id, name, message, image_key, expires_at, created_at
            FROM notices
            WHERE expires_at IS NULL OR expires_at > now()
            ORDER BY id DESC
            """
        )
    finally:
        conn.close()
    return {"notices": [row_to_notice(r) for r in rows]}


@router.post("/notices", status_code=201)
def create_notice(payload: NoticeCreate):
    name = payload.name.strip()
    message = payload.message.strip()
    if not name:
        raise HTTPException(400, "name is required")
    if not message:
        raise HTTPException(400, "message is required")
    if payload.expires_in not in EXPIRY_DURATIONS:
        raise HTTPException(400, f"invalid expires_in: {payload.expires_in!r}")

    duration = EXPIRY_DURATIONS[payload.expires_in]
    expires_at = datetime.now(timezone.utc) + duration if duration else None

    ensure_table()
    conn = get_connection()
    try:
        rows = conn.run(
            """
            INSERT INTO notices (name, message, image_key, expires_at)
            VALUES (:name, :message, :image_key, :expires_at)
            RETURNING id, name, message, image_key, expires_at, created_at
            """,
            name=name,
            message=message,
            image_key=payload.image_key,
            expires_at=expires_at,
        )
    finally:
        conn.close()
    return {"notice": row_to_notice(rows[0])}


@router.delete("/notices/{notice_id}")
def delete_notice(notice_id: str):
    try:
        notice_id_int = int(notice_id)
    except ValueError:
        raise HTTPException(404, "Notice not found")

    ensure_table()
    conn = get_connection()
    try:
        rows = conn.run("DELETE FROM notices WHERE id = :id RETURNING id", id=notice_id_int)
    finally:
        conn.close()
    if not rows:
        raise HTTPException(404, "Notice not found")
    return {"deleted": notice_id}
