# This file contains the FastAPI routes for authentication-related operations, including login, 
# token refresh, user registration, and manager verification. It defines the endpoints and 
# delegates the actual business logic to the `auth_service` module.
from fastapi import APIRouter, Depends, status

from app.models.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, VerifyManagerRequest
from app.models.user import UserInDB, UserOut
from app.security.deps import get_current_user
from app.services import auth_service

# the prefix "/auth" is used for all routes in this router, and the tag "auth" is used for documentation purposes.
router = APIRouter(prefix="/auth", tags=["auth"])

# The `login` endpoint allows users to log in by providing their email and password.
# It returns a pair of JWT tokens (access and refresh) if the credentials are valid.
@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest) -> TokenPair:
    return await auth_service.login(payload.email, payload.password)

# The `refresh` endpoint allows users to refresh their JWT tokens by providing a valid refresh token.
# It returns a new pair of JWT tokens (access and refresh) if the refresh token is
@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest) -> TokenPair:
    return await auth_service.refresh(payload.refresh_token)

# The `register` endpoint allows new users to register by providing their email, password, role, and an optional invite code.
# It returns the newly created user's information if the registration is successful.                
@router.post("/register", response_model=UserOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> UserOut:
    return await auth_service.register(payload)

# The `verify_manager` endpoint allows a manager to verify their account using an invite code.
# It returns the manager's information if the verification is successful.
@router.post("/verify-manager", response_model=UserOut, response_model_by_alias=False)
async def verify_manager(payload: VerifyManagerRequest) -> UserOut:
    return await auth_service.verify_manager(payload)

# The `me` endpoint returns the profile of whoever the access token belongs to.
# It exists because the JWT itself only carries the user's id and role (deliberately,
# to avoid stale/exposed data) - this is how the frontend gets the rest, like email,
# once it already knows someone is logged in.
@router.get("/me", response_model=UserOut, response_model_by_alias=False)
async def get_me(user: UserInDB = Depends(get_current_user)) -> UserOut:
    return UserOut(**user.model_dump(by_alias=True))