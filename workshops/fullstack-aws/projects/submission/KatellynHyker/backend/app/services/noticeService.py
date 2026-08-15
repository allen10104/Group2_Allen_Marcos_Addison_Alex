"""
Business logic for managing notices.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import NoticeORM, UserORM
from app.models.exceptions import ForbiddenError, NotFoundError
from app.models.schemas import NoticeCreate, NoticeUpdate

def list_notices(db: Session):
    """List every notice on the board, newest first. Shared board -- any
    authenticated user can see every notice, not just their own."""
    notices = db.execute(select(NoticeORM).order_by(NoticeORM.created_at.desc())).scalars().all()
    return notices

def get_notice(notice_id: str, db: Session):
    """Get a specific notice by ID. Any authenticated user may view it."""
    notice = db.get(NoticeORM, notice_id)
    if not notice:
        raise NotFoundError(f"Notice with ID {notice_id} not found.")
    return notice

def create_notice(request: NoticeCreate, db: Session, current_user: UserORM):
    """Create a new notice authored by the current user."""
    new_notice = NoticeORM(
        user_id=current_user.user_id, title=request.title, content=request.content
    )
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    return new_notice

def update_notice(notice_id: str, request: NoticeUpdate, db: Session, current_user: UserORM):
    """Update an existing notice. Only the notice's author may edit it."""
    notice = get_notice(notice_id, db)
    if notice.user_id != current_user.user_id:
        raise ForbiddenError("You can only edit your own notices.")

    if request.title is not None:
        notice.title = request.title
    if request.content is not None:
        notice.content = request.content

    db.commit()
    db.refresh(notice)
    return notice

def delete_notice(notice_id: str, db: Session, current_user: UserORM):
    """Delete a notice. Only the notice's author may delete it."""
    notice = get_notice(notice_id, db)
    if notice.user_id != current_user.user_id:
        raise ForbiddenError("You can only delete your own notices.")

    db.delete(notice)
    db.commit()