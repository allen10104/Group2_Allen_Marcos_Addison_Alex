# This file contains endpoints for managing invite codes in the noticeboard application.
from fastapi import APIRouter, Depends, status

from app.models.invite_code import InviteCodeCreate, InviteCodeOut
from app.models.user import Role, UserInDB
from app.security.deps import require_roles
from app.services import invite_service

router = APIRouter(prefix="/admin/invite-codes", tags=["invite-codes"])

# The `create_invite_code` endpoint allows a manager to generate a new invite code for a specific target email.
@router.post("", response_model=InviteCodeOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def create_invite_code(
    payload: InviteCodeCreate,
    manager: UserInDB = Depends(require_roles(Role.MANAGER)),
) -> InviteCodeOut:
    invite = await invite_service.generate_code(payload.target_email, manager)
    return InviteCodeOut(**invite.model_dump(by_alias=True))