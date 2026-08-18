# This file contains the business logic for user authentication, including login, registration, token refreshing, 
# and manager verification. It interacts with the database through the `users_repo` module and uses JWT tokens for authentication.
from bson import ObjectId
from fastapi import HTTPException, status

from app.data.users_repo import create_user, get_user_by_email, get_user_by_id, set_user_status
from app.models.auth import RegisterRequest, TokenPair, VerifyManagerRequest
from app.models.user import Role, UserOut, UserStatus
from app.security.jwt import TokenKind, create_access_token, create_refresh_token, decode_token
from app.security.passwords import hash_password, verify_password
from app.services import invite_service

# This function handles user login by verifying the provided email and password. 
# If the credentials are valid, it generates and returns a pair of JWT tokens (access and refresh).
async def login(email: str, password: str) -> TokenPair:
    user = await get_user_by_email(email)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.role == Role.MANAGER and user.status == UserStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager account pending verification")

    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
    )

# This function handles token refreshing by validating the provided refresh token.
# If the token is valid, it generates and returns a new pair of JWT tokens (access and refresh).
async def refresh(refresh_token: str) -> TokenPair:
    payload = decode_token(refresh_token, TokenKind.REFRESH)
    user = await get_user_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
    )

# This function handles user registration by creating a new user in the database.
# It checks for existing users, validates invite codes for managers, and sets the appropriate user status
async def register(payload: RegisterRequest) -> UserOut:
    existing = await get_user_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    if payload.role == Role.EMPLOYEE:
        user = await create_user(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=Role.EMPLOYEE,
            created_by=None,
            status=UserStatus.APPROVED,
        )
        return UserOut(**user.model_dump(by_alias=True))

    invite = None
    if payload.invite_code:
        invite = await invite_service.validate_code(payload.email, payload.invite_code)

    user = await create_user(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=Role.MANAGER,
        created_by=None,
        status=UserStatus.APPROVED if invite else UserStatus.PENDING,
    )

    if invite:
        await invite_service.consume_code(payload.invite_code, ObjectId(user.id))

    return UserOut(**user.model_dump(by_alias=True))

# This function handles the verification of a manager's invite code. It checks that the manager account is pending, 
# validates the invite code, and updates the user's status to approved if the code is valid.
async def verify_manager(payload: VerifyManagerRequest) -> UserOut:
    user = await get_user_by_email(payload.email)
    if user is None or user.role != Role.MANAGER or user.status != UserStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending manager account for this email")

    invite = await invite_service.validate_code(payload.email, payload.code)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or already-used invite code")

    await invite_service.consume_code(payload.code, ObjectId(user.id))
    updated = await set_user_status(user.id, UserStatus.APPROVED)
    return UserOut(**updated.model_dump(by_alias=True))