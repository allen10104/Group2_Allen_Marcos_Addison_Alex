import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.jwt_utils import create_access_token, decode_access_token
from backend.auth.passwords import hash_password, verify_password
from backend.models.user import User

# Stub users: passwords are bcrypt hashes, not plaintext.
# Login still uses the same demo passwords: "password" / "admin123".
USERS_BY_ID: dict[int, User] = {
    1: User(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        password_hash=hash_password("password"),
        is_admin=True,
    ),
    2: User(
        id=2,
        name="Jane Doe",
        email="jane.doe@example.com",
        password_hash=hash_password("password"),
        is_admin=False,
    ),
    3: User(
        id=3,
        name="Jim Doe",
        email="jim.doe@example.com",
        password_hash=hash_password("password"),
        is_admin=False,
    ),
    99: User(
        id=99,
        name="Admin",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        is_admin=True,
    ),
}

USERS_BY_EMAIL: dict[str, User] = {
    user.email.lower(): user for user in USERS_BY_ID.values()
}

bearer_scheme = HTTPBearer(auto_error=True)


def authenticate_user(email: str, password: str) -> User | None:
    user = USERS_BY_EMAIL.get(email.lower())
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    """Resolve the caller from Authorization: Bearer <jwt>."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = USERS_BY_ID.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_token_for_user(user: User) -> str:
    return create_access_token(
        user_id=user.id,
        email=user.email,
        is_admin=user.is_admin,
    )
