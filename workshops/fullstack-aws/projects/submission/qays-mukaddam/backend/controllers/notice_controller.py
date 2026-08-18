# APIRouter lets us define routes separately and plug them into main.py's app.
# HTTPException lets us return proper error responses. Depends is how
# FastAPI hands a database session to an endpoint.
from fastapi import APIRouter, HTTPException, Depends

# BaseModel defines the shape of the incoming request body.
from pydantic import BaseModel

# Session is the type hint for the database session object.
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from backend.database.session import get_db

# Import the service functions that contain the actual notice logic.
from backend.services.notice_service import create_notice, list_notices, delete_notice, get_notice_by_id

# count_likes lets us include a notice's like count in the response.
from backend.services.like_service import count_likes

# require_role restricts a route to specific roles. get_current_user
# allows any logged-in user through. CurrentUser is the type hint for
# whoever the token identifies as (now includes organization_id).
from backend.core.dependencies import require_role, get_current_user, CurrentUser


router = APIRouter()


class NoticeCreateRequest(BaseModel):
    name: str = None
    message: str = None


def notice_to_response(db: Session, notice):
    return {
        "id": notice.id,
        "name": notice.name,
        "message": notice.message,
        "created_at": str(notice.created_at),
        "view_count": notice.view_count,
        "like_count": count_likes(db, notice_id=notice.id),
    }


# POST /notices
# Creates a new notice on the ADMIN's OWN organization's board.
# organization_id comes from current_user, not from the request body —
# an admin has no way to post to a different organization's board.
@router.post("/notices", status_code=201)
def add_notice(
    request: NoticeCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    if not request.name or not request.message:
        raise HTTPException(status_code=400, detail="name and message are required")

    new_notice = create_notice(db, request.name, request.message, current_user.organization_id)

    return notice_to_response(db, new_notice)


# GET /notices
# Returns only notices belonging to the CURRENT USER's organization —
# this is what keeps each company's board private to its own members.
@router.get("/notices")
def get_all_notices(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    notices = list_notices(db, current_user.organization_id)

    return [notice_to_response(db, notice) for notice in notices]


# GET /notices/{notice_id}
# Fetches a single notice, but ONLY if it belongs to the current user's
# organization. If someone tries an id from a different org, it comes
# back as 404 — same response as if it didn't exist at all, so we don't
# even confirm to an attacker that a different org's notice with that
# id exists.
@router.get("/notices/{notice_id}")
def get_single_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    notice = get_notice_by_id(db, notice_id, current_user.organization_id)

    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")

    return notice_to_response(db, notice)


# DELETE /notices/{notice_id}
# Same organization check as above — an admin can only delete notices
# that belong to their own organization.
@router.delete("/notices/{notice_id}")
def remove_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN")),
):
    was_deleted = delete_notice(db, notice_id, current_user.organization_id)

    if not was_deleted:
        raise HTTPException(status_code=404, detail="Notice not found")

    return {"message": "Notice deleted", "id": notice_id}