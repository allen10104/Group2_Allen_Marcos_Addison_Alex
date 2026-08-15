"""
Business logic for comments on notices.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import CommentORM, UserORM
from app.models.exceptions import ForbiddenError, NotFoundError
from app.models.schemas import CommentCreate, CommentUpdate
from app.services.noticeService import get_notice

def list_comments(notice_id: str, db: Session):
    """List every comment on a notice, oldest first. Confirms the notice
    itself exists first so a bad notice_id 404s instead of just
    returning an empty list."""
    get_notice(notice_id, db)
    query = (
        select(CommentORM)
        .where(CommentORM.notice_id == notice_id)
        .order_by(CommentORM.created_at.asc())
    )
    return db.execute(query).scalars().all()

def get_comment(comment_id: str, db: Session):
    """Get a specific comment by ID."""
    comment = db.get(CommentORM, comment_id)
    if not comment:
        raise NotFoundError(f"Comment with ID {comment_id} not found.")
    return comment

def create_comment(notice_id: str, request: CommentCreate, db: Session, current_user: UserORM):
    """Add a comment to a notice. Any authenticated user may comment."""
    get_notice(notice_id, db)
    new_comment = CommentORM(
        notice_id=notice_id, user_id=current_user.user_id, content=request.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

def update_comment(comment_id: str, request: CommentUpdate, db: Session, current_user: UserORM):
    """Edit a comment. Only the comment's author may edit it."""
    comment = get_comment(comment_id, db)
    if comment.user_id != current_user.user_id:
        raise ForbiddenError("You can only edit your own comments.")

    comment.content = request.content
    db.commit()
    db.refresh(comment)
    return comment

def delete_comment(comment_id: str, db: Session, current_user: UserORM):
    """Delete a comment. Only the comment's author may delete it."""
    comment = get_comment(comment_id, db)
    if comment.user_id != current_user.user_id:
        raise ForbiddenError("You can only delete your own comments.")

    db.delete(comment)
    db.commit()