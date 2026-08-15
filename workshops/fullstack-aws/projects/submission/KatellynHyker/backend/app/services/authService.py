"""
Business logic for authentication and authorization.
"""

from sqlalchemy.orm import Session

from app.models.database import UserORM
from app.models.exceptions import DuplicateUserException, UnauthorizedException
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token

def register_user(db: Session, email: str, password: str) -> UserORM:
    """Create a new user with the given email and password."""
    existing_user = db.query(UserORM).filter(UserORM.email == email).first()
    if existing_user:
        raise DuplicateUserException(f"User with email {email} already exists.")

    hashed_password = hash_password(password)
    new_user = UserORM(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def login_user(db: Session, email: str, password: str) -> str:
    """Authenticate a user and return a JWT access token."""
    user = db.query(UserORM).filter(UserORM.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password.")

    access_token = create_access_token(data={"sub": user.user_id, "email": user.email})
    return access_token