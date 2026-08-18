# This file contains the business logic for notice management, including creating notices, 
# approving/rejecting them, acknowledging them, and checking read status.
# It interacts with the database through the `notices_repo` and `users_repo` modules.
from bson import ObjectId
from fastapi import HTTPException, status

from app.data.notices_repo import (
    add_read_receipt,
    create_notice,
    get_notice,
    list_notices,
    set_notice_decision,
)
from app.data.users_repo import list_all_employee_ids, list_employee_emails_by_ids
from app.models.notice import NoticeCreate, NoticeInDB, NoticeOut, NoticeStatus, ReadStatusOut
from app.models.user import Role, UserInDB

# the private function `_to_out` converts a `NoticeInDB` object to a `NoticeOut` object, which is the format used for API responses.
def _to_out(notice: NoticeInDB, viewer_id: ObjectId) -> NoticeOut:
    read_ids = {receipt.user_id for receipt in notice.read_by}
    return NoticeOut(
        _id=notice.id,
        title=notice.title,
        body=notice.body,
        category=notice.category,
        status=notice.status,
        author_id=notice.author_id,
        created_at=notice.created_at,
        approved_by=notice.approved_by,
        approved_at=notice.approved_at,
        read_count=len(read_ids),
        read_by_me=ObjectId(viewer_id) in read_ids,
    )

# The `submit_notice` function allows a user to submit a new notice.
async def submit_notice(payload: NoticeCreate, author: UserInDB) -> NoticeOut:
    status_ = NoticeStatus.APPROVED if author.role == Role.MANAGER else NoticeStatus.PENDING
    notice = await create_notice(
        title=payload.title,
        body=payload.body,
        category=payload.category,
        status=status_,
        author_id=ObjectId(author.id),
    )
    return _to_out(notice, author.id)

# The `get_feed` function retrieves a list of notices for a user, filtering based on their role.
async def get_feed(viewer: UserInDB) -> list[NoticeOut]:
    status_filter = None if viewer.role == Role.MANAGER else NoticeStatus.APPROVED
    notices = await list_notices(status_filter)
    return [_to_out(n, viewer.id) for n in notices]

# The `approve_notice` function allows a manager to approve a pending notice.
async def approve_notice(notice_id: str, manager: UserInDB) -> NoticeOut:
    notice = await set_notice_decision(notice_id, NoticeStatus.APPROVED, ObjectId(manager.id))
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending notice not found")
    return _to_out(notice, manager.id)

# The `reject_notice` function allows a manager to reject a pending notice.
async def reject_notice(notice_id: str, manager: UserInDB) -> NoticeOut:
    notice = await set_notice_decision(notice_id, NoticeStatus.REJECTED, ObjectId(manager.id))
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending notice not found")
    return _to_out(notice, manager.id)

# The `acknowledge_notice` function allows an employee to acknowledge (mark as read) an approved notice.
async def acknowledge_notice(notice_id: str, employee: UserInDB) -> NoticeOut:
    notice = await get_notice(notice_id)
    if notice is None or notice.status != NoticeStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")

    await add_read_receipt(notice_id, ObjectId(employee.id))

    refreshed = await get_notice(notice_id)
    return _to_out(refreshed, employee.id)

## The `read_status` function allows a manager to view the read/unread status of a notice.
async def read_status(notice_id: str, manager: UserInDB) -> ReadStatusOut:
    notice = await get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")

    all_employee_ids = await list_all_employee_ids()
    read_ids = {receipt.user_id for receipt in notice.read_by}
    unread_ids = [uid for uid in all_employee_ids if uid not in read_ids]

    read_emails = await list_employee_emails_by_ids(list(read_ids))
    unread_emails = await list_employee_emails_by_ids(unread_ids)

    return ReadStatusOut(
        notice_id=notice.id,
        total_employees=len(all_employee_ids),
        read_count=len(read_ids),
        read_emails=read_emails,
        unread_emails=unread_emails,
    )