from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_current_user
from backend.models.category import Category
from backend.models.user import User
from backend.schemas.notice import (
    NoticeCreateSchema,
    NoticeOutSchema,
    NoticeUpdateSchema,
    notice_to_out,
)
from backend.services.notice_service import notice_service

router = APIRouter(prefix="/api/v1", tags=["notices"])


def _http_error_from_value_error(exc: ValueError) -> HTTPException:
    """Domain ValueError → HTTP status. Service stays HTTP-free."""
    message = str(exc)
    if "not found" in message.lower():
        return HTTPException(status_code=404, detail=message)
    if "not authorized" in message.lower():
        return HTTPException(status_code=403, detail=message)
    return HTTPException(status_code=400, detail=message)


@router.post("/notices", status_code=201, response_model=NoticeOutSchema)
def create_notice(
    notice: NoticeCreateSchema,
    current_user: User = Depends(get_current_user),
) -> NoticeOutSchema:
    try:
        notice_date = notice.date.date().isoformat() if notice.date else None
        created = notice_service.create_notice(
            title=notice.title,
            content=notice.content,
            category=notice.category,
            actor=current_user,
            notice_date=notice_date,
        )
        return notice_to_out(created)
    except ValueError as e:
        raise _http_error_from_value_error(e) from e


@router.get("/notices", status_code=200, response_model=list[NoticeOutSchema])
def get_all_notices(
    q: str | None = None,
    author: str | None = None,
    author_id: int | None = None,
    category: Category | None = None,
) -> list[NoticeOutSchema]:
    try:
        notices = notice_service.list_notices(
            q=q,
            author=author,
            author_id=author_id,
            category=category,
        )
        return [notice_to_out(notice) for notice in notices]
    except ValueError as e:
        raise _http_error_from_value_error(e) from e


@router.get("/notices/{notice_id}", status_code=200, response_model=NoticeOutSchema)
def get_notice_by_id(notice_id: int) -> NoticeOutSchema:
    try:
        return notice_to_out(notice_service.get_notice(notice_id))
    except ValueError as e:
        raise _http_error_from_value_error(e) from e


@router.put("/notices/{notice_id}", status_code=200, response_model=NoticeOutSchema)
def update_notice(
    notice_id: int,
    notice: NoticeUpdateSchema,
    current_user: User = Depends(get_current_user),
) -> NoticeOutSchema:
    try:
        updates = notice.model_dump(exclude_unset=True)
        if "date" in updates and updates["date"] is not None:
            updates["date"] = updates["date"].date().isoformat()
        updated = notice_service.update_notice(notice_id, current_user, **updates)
        return notice_to_out(updated)
    except ValueError as e:
        raise _http_error_from_value_error(e) from e


@router.delete("/notices/{notice_id}", status_code=200)
def delete_notice(
    notice_id: int,
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        notice_service.delete_notice(notice_id, current_user)
        return {"deleted": notice_id}
    except ValueError as e:
        raise _http_error_from_value_error(e) from e
