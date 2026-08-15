"""
Builds the comment service for the NoticeBoard application. This service handles operations related to comments, including creating, retrieving, updating, and deleting comments associated with notices. It interacts with the database models and provides an interface for the controllers to manage comment data.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import CommentORM, UserORM
from app.models.exceptions import ForbiddenError, NotFoundError
from app.models.schemas import CommentCreate, CommentUpdate
from app.services.noticeService import get_notice

def list_comments(db: Session, notice_id: str):
    """
    List all comments for a given notice.
    """
    # Ensure the notice exists
    get_notice(db, notice_id)

    query = (
        select(CommentORM)
        .where(CommentORM.notice_id == notice_id)
        .order_by(CommentORM.created_at.asc())
    )
    return db.execute(query).scalars().all()

def get_comment(db: Session, comment_id: str):
    """
    Retrieve a specific comment by its ID.
    """
    comment = db.get(CommentORM, comment_id)
    if not comment:
        raise NotFoundError(f"Comment with ID {comment_id} not found.")
    return comment

def create_comment(db: Session, notice_id: str, user_id: str, comment_data: CommentCreate):
    """
    Create a new comment for a given notice.
    """
    # Ensure the notice exists
    get_notice(db, notice_id)

    new_comment = CommentORM(
        content=comment_data.content,
        notice_id=notice_id,
        user_id=user_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

def update_comment(db: Session, comment_id: str, user_id: str, comment_data: CommentUpdate):
    """
    Update an existing comment. Only the author of the comment can update it.
    """
    comment = get_comment(db, comment_id)

    if comment.user_id != user_id:
        raise ForbiddenError("You do not have permission to update this comment.")

    comment.content = comment_data.content
    db.commit()
    db.refresh(comment)
    return comment

def delete_comment(db: Session, comment_id: str, user_id: str):
    """
    Delete an existing comment. Only the author of the comment can delete it.
    """
    comment = get_comment(db, comment_id)

    if comment.user_id != user_id:
        raise ForbiddenError("You do not have permission to delete this comment.")

    db.delete(comment)
    db.commit()
