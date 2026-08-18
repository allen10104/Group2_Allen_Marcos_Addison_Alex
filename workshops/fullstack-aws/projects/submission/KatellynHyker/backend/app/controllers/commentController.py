""" Route handlers for comments on notices. """

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import UserORM, get_db
from app.models.schemas import CommentCreate, CommentUpdate
from app.security.dependencies import get_current_user
from app.services import commentService

notice_comments_router = APIRouter(prefix="/notice", tags=["comments"])
comments_router = APIRouter(prefix="/comments", tags=["comments"])

@notice_comments_router.get("/{notice_id}/comments")
def list_comments(notice_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    comments = commentService.list_comments(notice_id, db)
    return [c.to_dict() for c in comments]

@notice_comments_router.post("/{notice_id}/comments", status_code=201)
def create_comment(notice_id: str, request: CommentCreate, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    comment = commentService.create_comment(notice_id, request, db, current_user)
    return comment.to_dict()

@comments_router.put("/{comment_id}")
def update_comment(comment_id: str, request: CommentUpdate, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    comment = commentService.update_comment(comment_id, request, db, current_user)
    return comment.to_dict()

@comments_router.delete("/{comment_id}", status_code=204)
def delete_comment(comment_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    commentService.delete_comment(comment_id, db, current_user)