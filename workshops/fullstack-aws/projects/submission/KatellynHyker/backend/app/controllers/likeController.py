""" Route handlers for liking notices. """

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import UserORM, get_db
from app.security.dependencies import get_current_user
from app.services import likeService

router = APIRouter(prefix="/notice", tags=["likes"])

@router.get("/{notice_id}/likes")
def get_like_summary(notice_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    return likeService.get_like_summary(notice_id, db, current_user)

@router.post("/{notice_id}/like", status_code=204)
def like_notice(notice_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    likeService.like_notice(notice_id, db, current_user)

@router.delete("/{notice_id}/like", status_code=204)
def unlike_notice(notice_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    likeService.unlike_notice(notice_id, db, current_user)