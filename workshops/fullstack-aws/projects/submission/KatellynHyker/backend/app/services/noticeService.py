"""
Business logic for managing notices.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import NoticeORM, UserORM
from app.models.exceptions import NotFoundException, UnauthorizedException

def list_notices(db: Session, user_id: int):
    """List all notices for a given user."""
    user = db.get(UserORM, user_id)
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found.")

    notices = db.execute(select(NoticeORM).where(NoticeORM.user_id == user_id)).scalars().all()
    return notices

def get_notice(db: Session, notice_id: int, user_id: int):
    """Get a specific notice by ID for a given user."""
    notice = db.get(NoticeORM, notice_id)
    if not notice:
        raise NotFoundException(f"Notice with ID {notice_id} not found.")
    if notice.user_id != user_id:
        raise UnauthorizedException("You do not have permission to access this notice.")
    return notice

def create_notice(db: Session, user_id: int, title: str, content: str):
    """Create a new notice for a given user."""
    user = db.get(UserORM, user_id)
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found.")

    new_notice = NoticeORM(user_id=user_id, title=title, content=content)
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    return new_notice

def update_notice(db: Session, notice_id: int, user_id: int, title: str = None, content: str = None):
    """Update an existing notice for a given user."""
    notice = db.get(NoticeORM, notice_id)
    if not notice:
        raise NotFoundException(f"Notice with ID {notice_id} not found.")
    if notice.user_id != user_id:
        raise UnauthorizedException("You do not have permission to update this notice.")

    if title is not None:
        notice.title = title
    if content is not None:
        notice.content = content

    db.commit()
    db.refresh(notice)
    return notice

def delete_notice(db: Session, notice_id: int, user_id: int):
    """Delete a notice for a given user."""
    notice = db.get(NoticeORM, notice_id)
    if not notice:
        raise NotFoundException(f"Notice with ID {notice_id} not found.")
    if notice.user_id != user_id:
        raise UnauthorizedException("You do not have permission to delete this notice.")

    db.delete(notice)
    db.commit()
    return notice