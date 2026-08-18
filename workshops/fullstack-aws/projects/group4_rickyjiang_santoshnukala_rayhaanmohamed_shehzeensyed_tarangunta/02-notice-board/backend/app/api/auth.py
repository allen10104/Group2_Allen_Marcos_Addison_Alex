"""Authentication routes."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.dependencies import get_auth_service
from app.domain.enums import Role
from app.schemas.auth import CurrentUser, LoginRequest, LoginResponse
from app.security.deps import get_current_user, require_admin
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    employee_id: str
    username: str = Field(min_length=3, max_length=40)
    # A minimum LENGTH is the one password rule worth enforcing. Composition rules
    # ("one uppercase, one symbol") demonstrably push users toward "Passw0rd!";
    # NIST 800-63B recommends length over composition.
    password: str = Field(min_length=8)
    full_name: str
    department: str | None = None
    roles: list[Role] | None = None


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """Public. Returns the JWT the frontend carries on every later request."""
    return service.login(payload)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    _admin: CurrentUser = Depends(require_admin),   # the role gate
    service: AuthService = Depends(get_auth_service),
):
    """ADMIN only. At a bank, staff accounts are provisioned, not self-registered."""
    created = service.register(
        employee_id=payload.employee_id,
        username=payload.username,
        password=payload.password,
        full_name=payload.full_name,
        department=payload.department,
        roles=set(payload.roles) if payload.roles else None,
    )
    return {"id": created.id, "username": created.username, "message": "Employee registered"}


@router.get("/me", response_model=CurrentUser)
def me(current: CurrentUser = Depends(get_current_user)):
    """Who does the server think I am?

    The single most useful endpoint for debugging auth. When a request returns an
    unexpected status, hitting /me tells you instantly whether the token parsed at all
    and which identity the server actually sees.
    """
    return current
