# This file contains endpoints for managing notices in the noticeboard application.

from fastapi import APIRouter, Depends, status

from app.models.notice import NoticeCreate, NoticeOut, ReadStatusOut
from app.models.user import Role, UserInDB
from app.security.deps import get_current_user, require_roles
from app.services import notice_service

router = APIRouter(prefix="/notices", tags=["notices"])

# The `submit_notice` endpoint allows a user to submit a new notice by providing the notice details.
@router.post("", response_model=NoticeOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def submit_notice(
    payload: NoticeCreate,
    user: UserInDB = Depends(get_current_user),
) -> NoticeOut:
    return await notice_service.submit_notice(payload, user)

# The `get_feed` endpoint retrieves a list of notices for the current user, filtering based on their role.
@router.get("", response_model=list[NoticeOut], response_model_by_alias=False)
async def get_feed(user: UserInDB = Depends(get_current_user)) -> list[NoticeOut]:
    return await notice_service.get_feed(user)

# The `acknowledge_notice` endpoint allows an employee to acknowledge that they have read a specific notice.
@router.post("/{notice_id}/approve", response_model=NoticeOut, response_model_by_alias=False)
async def approve_notice(
    notice_id: str,
    manager: UserInDB = Depends(require_roles(Role.MANAGER)),
) -> NoticeOut:
    return await notice_service.approve_notice(notice_id, manager)

# The `reject_notice` endpoint allows a manager to reject a specific notice.
@router.post("/{notice_id}/reject", response_model=NoticeOut, response_model_by_alias=False)
async def reject_notice(
    notice_id: str,
    manager: UserInDB = Depends(require_roles(Role.MANAGER)),
) -> NoticeOut:
    return await notice_service.reject_notice(notice_id, manager)

# The `acknowledge_notice` endpoint allows an employee to acknowledge (mark as read) a specific notice.
@router.post("/{notice_id}/ack", response_model=NoticeOut, response_model_by_alias=False)
async def acknowledge_notice(
    notice_id: str,
    employee: UserInDB = Depends(require_roles(Role.EMPLOYEE)),
) -> NoticeOut:
    return await notice_service.acknowledge_notice(notice_id, employee)

# The `read_status` endpoint allows a manager to view the read/unread status of a specific notice.
@router.get("/{notice_id}/read-status", response_model=ReadStatusOut)
async def read_status(
    notice_id: str,
    manager: UserInDB = Depends(require_roles(Role.MANAGER)),
) -> ReadStatusOut:
    return await notice_service.read_status(notice_id, manager)