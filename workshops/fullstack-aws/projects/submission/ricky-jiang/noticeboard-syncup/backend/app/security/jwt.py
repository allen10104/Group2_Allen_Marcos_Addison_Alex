# Everywhere we use JWTs, we need to create them and decode them. This file contains the functions to do that.

from datetime import datetime, timedelta, timezone
from enum import Enum

import jwt
from fastapi import HTTPException, status

from app.config import settings

# This tags each token as either access or refresh
# Decode_token checks that the token is the expected type, and raises an error if it is not. 
# This prevents a refresh token from being used as an access token, or vice versa.
class TokenKind(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"

# A private function that creates a JWT with the given subject, role, kind (access or refresh), and expiration time.
# Payload is the actual data stored in the JWT
def _create_token(subject: str, role: str, kind: TokenKind, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "type": kind.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    # This signs the payload with the secret key and algorithm specified in the settings, and returns the encoded JWT as a string.
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

# Calls create_token with the access token expiration time specified in the settings, and returns the encoded JWT as a string.
def create_access_token(subject: str, role: str) -> str:
    return _create_token(
        subject, role, TokenKind.ACCESS, timedelta(minutes=settings.access_token_expire_minutes)
    )

# Calls create_token with the refresh token expiration time specified in the settings, and returns the encoded JWT as a string.
def create_refresh_token(subject: str, role: str) -> str:
    return _create_token(
        subject, role, TokenKind.REFRESH, timedelta(days=settings.refresh_token_expire_days)
    )

# This function decodes a JWT and checks that it is the expected type (access or refresh).
def decode_token(token: str, expected_kind: TokenKind) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != expected_kind.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    return payload