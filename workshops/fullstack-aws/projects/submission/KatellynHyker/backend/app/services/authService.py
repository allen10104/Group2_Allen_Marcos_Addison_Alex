"""
Business logic for authentication and authorization.
"""

from sqlalchemy.orm import Session

from app.models.database import UserORM
from app.models.exceptions import DuplicateError, UnauthorizedError
from app.models.schemas import LoginRequest, RegisterRequest
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token

def register(request: RegisterRequest, db: Session) -> dict:
    """Create a new user account and return it with an access token."""
    existing_user = db.query(UserORM).filter(UserORM.email == request.email).first()
    if existing_user:
        raise DuplicateError(f"An account with email '{request.email}' already exists.")

    new_user = UserORM(email=request.email, hashed_password=hash_password(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(new_user)
    return {"user": new_user.to_dict(), "access_token": token, "token_type": "bearer"}

def login(request: LoginRequest, db: Session) -> dict:
    """Validate credentials and return the user with an access token."""
    user = db.query(UserORM).filter(UserORM.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        # Deliberately the same error for "no such user" and "wrong password"
        # -- distinguishing them would let an attacker enumerate valid emails.
        raise UnauthorizedError("Invalid email or password.")

    token = create_access_token(user)
    return {"user": user.to_dict(), "access_token": token, "token_type": "bearer"}