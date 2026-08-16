from fastapi import APIRouter, HTTPException

from app.models.notice import NoticeCreate
from app.services.notice_service import (
    add_notice,
    list_notices,
    remove_notice,
)

# Groups all of the notice endpoints under /notices
router = APIRouter(
    prefix="/notices",
    tags=["Notices"],
)


# Returns all notices from the database
@router.get("")
def get_notices():
    return list_notices()


# Creates a new notice using the data sent by the frontend
@router.post("", status_code=201)
def post_notice(notice: NoticeCreate):
    return add_notice(
        notice.name,
        notice.message,
        notice.priority,
    )


# Deletes a specific notice using its ID
@router.delete("/{notice_id}")
def delete_notice(notice_id: str):
    deleted = remove_notice(notice_id)

    # Returns a 404 if the notice does not exist
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Notice not found",
        )

    return {
        "message": "Notice deleted successfully"
    }