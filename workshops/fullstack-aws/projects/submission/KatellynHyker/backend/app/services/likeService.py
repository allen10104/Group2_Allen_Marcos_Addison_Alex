"""
Business logic for liking notices.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.database import LikeORM, UserORM
from app.services.noticeService import get_notice

def get_like_summary(notice_id: str, db: Session, current_user: UserORM):
    """Return the like count for a notice and whether the current user
    has liked it."""
    get_notice(notice_id, db)
    count = db.execute(
        select(func.count()).select_from(LikeORM).where(LikeORM.notice_id == notice_id)
    ).scalar_one()
    liked_by_me = db.get(LikeORM, (current_user.user_id, notice_id)) is not None
    return {"notice_id": notice_id, "like_count": count, "liked_by_me": liked_by_me}

def like_notice(notice_id: str, db: Session, current_user: UserORM):
    """Like a notice. Idempotent -- liking a notice you've already liked
    is a no-op rather than an error."""
    get_notice(notice_id, db)
    existing = db.get(LikeORM, (current_user.user_id, notice_id))
    if existing:
        return
    new_like = LikeORM(user_id=current_user.user_id, notice_id=notice_id)
    db.add(new_like)
    db.commit()

def unlike_notice(notice_id: str, db: Session, current_user: UserORM):
    """Unlike a notice. Idempotent -- unliking a notice you haven't
    liked is a no-op rather than an error."""
    like = db.get(LikeORM, (current_user.user_id, notice_id))
    if not like:
        return
    db.delete(like)
    db.commit()