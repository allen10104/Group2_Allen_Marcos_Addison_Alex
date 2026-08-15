""" Routes for /api/notice endpoints """

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import UserORM, get_db
from app.models.schemas import NoticeCreate, NoticeUpdate
from app.security.dependencies import get_current_user
from app.services import noticeService

router = APIRouter(prefix="/notice", tags=["notice"])

@router.get("")
def list_notices(db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    notices = noticeService.list_notices(db)
    return [n.to_dict() for n in notices]

@router.get("/{notice_id}")
def get_notice(notice_id: int, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    notice = noticeService.get_notice(notice_id, db)
    return notice.to_dict()

@router.post("", status_code=201)
def create_notice(request: NoticeCreate, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    notice = noticeService.create_notice(request, db, current_user)
    return notice.to_dict()

@router.put("/{notice_id}")
def update_notice(notice_id: int, request: NoticeUpdate, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    notice = noticeService.update_notice(notice_id, request, db, current_user)
    return notice.to_dict()

@router.delete("/{notice_id}", status_code=204)
def delete_notice(notice_id: int, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    noticeService.delete_notice(notice_id, db, current_user)