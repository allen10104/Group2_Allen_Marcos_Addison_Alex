"""
Notice Board API — FastAPI, running on Lambda behind API Gateway via Mangum.

Endpoints:
    POST   /auth/register   {username, password} -> {access_token}
    POST   /auth/login      {username, password} -> {access_token}
    GET    /notices                                -> public, list notices
    POST   /notices         {message}  [auth required] -> create notice
    DELETE /notices/{id}    [auth required]            -> delete notice

Connection details come from environment variables:
    PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD, JWT_SECRET
    (optional) JWT_EXPIRE_MINUTES, default 60

Do not modify this file when working on Tier 4 (observability) — that
tier is implemented entirely in Terraform / infrastructure.
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import psycopg2
import psycopg2.errors
import psycopg2.extras
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mangum import Mangum
from pydantic import BaseModel, Field

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))

# Comma-separated usernames granted admin permissions (can edit/delete any
# notice, pin/unpin any notice). Set via the ADMIN_USERNAMES env var.
ADMIN_USERNAMES = {u.strip() for u in os.environ.get("ADMIN_USERNAMES", "").split(",") if u.strip()}

app = FastAPI(title="Notice Board API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

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
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
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


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NoticeCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class NoticeUpdate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class NoticePinUpdate(BaseModel):
    pinned: bool


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "is_admin": username in ADMIN_USERNAMES,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_username(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return get_current_user(creds)["username"]


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return {"username": payload["sub"], "is_admin": bool(payload.get("is_admin", False))}


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest):
    conn = get_connection()
    try:
        ensure_tables(conn)
        password_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (body.username, password_hash),
                )
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
        conn.commit()
        return TokenResponse(access_token=create_access_token(body.username))
    finally:
        conn.close()


@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (body.username,))
            row = cur.fetchone()
        if not row or not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
        return TokenResponse(access_token=create_access_token(body.username))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Notice routes
# ---------------------------------------------------------------------------

NOTICE_FIELDS = "id, message, author, pinned, created_at, updated_at"


def _serialize_notice(row: dict) -> dict:
    row["created_at"] = row["created_at"].isoformat()
    row["updated_at"] = row["updated_at"].isoformat() if row["updated_at"] else None
    return row


@app.get("/notices")
def list_notices():
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"SELECT {NOTICE_FIELDS} FROM notices ORDER BY pinned DESC, created_at DESC"
            )
            rows = cur.fetchall()
        return [_serialize_notice(row) for row in rows]
    finally:
        conn.close()


@app.post("/notices", status_code=201)
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


@app.put("/notices/{notice_id}")
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


@app.patch("/notices/{notice_id}/pin")
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


@app.delete("/notices/{notice_id}")
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


handler = Mangum(app, lifespan="off")
