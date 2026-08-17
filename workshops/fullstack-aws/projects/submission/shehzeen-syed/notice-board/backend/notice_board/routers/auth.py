"""
Registration and login endpoints.

Both issue a JWT on success; there's no server-side session state, so
"logging out" is purely a frontend action (discarding the stored token).
"""

import psycopg2
import psycopg2.errors
import psycopg2.extras
from fastapi import APIRouter, HTTPException, status

from ..database import ensure_tables, get_connection
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest):
    conn = get_connection()
    try:
        ensure_tables(conn)
        password_hash = hash_password(body.password)
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (body.username, body.email, password_hash),
                )
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
        conn.commit()
        return TokenResponse(access_token=create_access_token(body.username))
    finally:
        conn.close()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (body.username,))
            row = cur.fetchone()
        if not row or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
        return TokenResponse(access_token=create_access_token(body.username))
    finally:
        conn.close()
