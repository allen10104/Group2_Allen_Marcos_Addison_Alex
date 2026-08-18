# This is where the JWT are enforced. It contains the dependencies that are used to get the current user and check their role.

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.data.users_repo import get_user_by_id
from app.models.auth import TokenData
from app.models.user import Role, UserInDB
from app.security.jwt import TokenKind, decode_token

# HTTPBearer is a FastAPI class that extracts the Authorization header from the request and checks that it is a Bearer token.
_bearer_scheme = HTTPBearer(auto_error=True)

# Identifies the user that is making the request by decoding the JWT in the Authorization header and looking up the user in the database.
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserInDB:
    payload = decode_token(credentials.credentials, TokenKind.ACCESS)
    token_data = TokenData(sub=payload["sub"], role=payload["role"])

    if not ObjectId.is_valid(token_data.sub):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject")

    user = await get_user_by_id(token_data.sub)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

# This dependency checks that the current user has one of the specified roles. If the user does not have the required role, it raises a 403 Forbidden error.
def require_roles(*roles: Role):
    async def _check(user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _check