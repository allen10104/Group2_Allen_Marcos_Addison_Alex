"""The authentication dependency."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.enums import Role
from app.schemas.auth import CurrentUser
from app.security.jwt_service import decode_access_token

# auto_error=False so a MISSING header returns None instead of FastAPI raising its own
# 403. We want to raise 401 ourselves, with our ApiError body and the WWW-Authenticate
# header the spec requires. 401-vs-403 matters: the frontend redirects to login on 401
# and shows "insufficient permissions" on 403.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """Resolve the caller from the Bearer token, or reject with 401.

    Any route declaring `me: CurrentUser = Depends(get_current_user)` is now protected,
    and FastAPI shows a padlock next to it in /docs automatically.

    WHY A DEPENDENCY, NOT MIDDLEWARE: middleware runs on every request including /docs
    and /api/health, so you would need a path-exclusion list that rots. A dependency is
    declared per route - the requirement is visible in the function signature.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required - send a valid Bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or not credentials.credentials:
        raise unauthorized

    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        # Expected and common - a user left a tab open. Not an incident.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired - please sign in again",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        # Bad signature, malformed token, wrong algorithm.
        raise unauthorized

    # Unknown roles are dropped rather than raising. A token claiming
    # roles:["SUPERADMIN"] ends up with no authority at all instead of a 500.
    # Fail closed, not loud.
    roles = []
    for raw in claims.get("roles", []):
        try:
            roles.append(Role(raw))
        except ValueError:
            continue

    return CurrentUser(
        username=claims.get("sub", ""),
        employee_id=claims.get("employee_id", ""),
        full_name=claims.get("full_name"),
        department=claims.get("department"),
        roles=roles,
    )


def require_admin(me: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Layered dependency: authenticate first, then check the role.

    Used only on /api/auth/register. Flat permissions on NOTICES does not mean flat
    permissions on ACCOUNTS - letting any employee mint an account is a different and
    much worse problem than letting them post a notice.
    """
    if not me.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return me
