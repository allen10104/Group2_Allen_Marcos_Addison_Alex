"""
FastAPI dependencies for security-related functionality, such as authentication and authorization.
"""

import jwt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models.database import UserORM, get_db
from app.models.exceptions import UnauthorizedError
from app.security.tokens import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise UnauthorizedError("Missing authorization credentials.")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as e:
        raise UnauthorizedError(str(e))

    user = db.get(UserORM, payload.get("sub"))
    if user is None:
        raise UnauthorizedError("User not found.")
    return user