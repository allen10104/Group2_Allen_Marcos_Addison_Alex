"""
Password hashing and JWT-based authentication.

Tokens carry both the username (`sub`) and an `is_admin` flag computed
at issue time from ADMIN_USERNAMES, so protected routes can check
permissions straight from the token without a second database lookup.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import ADMIN_USERNAMES, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "is_admin": username in ADMIN_USERNAMES,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency: decodes the bearer token into {username, is_admin}.
    Add `user: dict = Depends(get_current_user)` to a route to require auth.
    """
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return {"username": payload["sub"], "is_admin": bool(payload.get("is_admin", False))}
