# Depends is how FastAPI injects a value into an endpoint. HTTPException
# lets us return proper error responses. status holds standard HTTP codes.
from fastapi import Depends, HTTPException, status

# HTTPBearer reads the "Authorization: Bearer <token>" header and shows
# Swagger a single "paste your token" field, with no username/password form. 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from backend.database.session import get_db

# decode_access_token verifies the JWT and returns its payload, or None.
from backend.core.security import decode_access_token

from backend.models.user import User

# The scheme Swagger's "Authorize" button uses for protected routes.
bearer_scheme = HTTPBearer()


# A small object holding the identity of whoever's making the request,
# so controllers don't have to keep re-querying the User table themselves. also carries organization_id, so controllers can scope queries
# (e.g. "only this user's organization's notices") without a separate
# database lookup.
class CurrentUser:
    def __init__(self, user_id: int, username: str, role: str, organization_id: int):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.organization_id = organization_id

    # Convenience method for role checks in controllers.
    def has_role(self, role_name: str) -> bool:
        return self.role == role_name


# Verifies the JWT sent with the request and returns a CurrentUser.
# Raises 401 if the token is missing, invalid, expired, or the user no
# longer exists.
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> CurrentUser:
    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # "sub" (subject) holds the user's id, set when the token was created.
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Build CurrentUser straight from the User row, which already has
    # organization_id on it — no need to pull org_id out of the token
    # payload separately.
    return CurrentUser(user.id, user.username, user.role, user.organization_id)


# Builds a dependency that only allows specific roles through.
# Usage: Depends(require_role("ADMIN"))
def require_role(*allowed_roles: str):
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this action")
        return current_user

    return role_checker