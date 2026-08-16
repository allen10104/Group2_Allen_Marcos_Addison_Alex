from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
import models, schemas, database, auth
from sqlalchemy.orm import Session
from models import Department
from datetime import datetime
from fastapi import APIRouter

router = APIRouter(prefix="/notices", tags=["notices"])
@router.get("/", response_model=List[schemas.NoticeResponse], status_code=status.HTTP_200_OK)
def get_all_notices(
    department: Optional[Department] = None,
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Notice)
    if department:
        query = query.filter(models.Notice.department == department)
    return query.order_by(models.Notice.created_at.desc()).all()


@router.get("/feed", response_model=List[schemas.NoticeResponse], status_code=status.HTTP_200_OK)
def get_relevant_notices(
    skip: int = 0,
    limit: int = 50,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Notices tagged for the current user's own department or the whole company."""
    notices = (
        db.query(models.Notice)
        .filter(models.Notice.department.in_([current_user.department, Department.ALL_EMPLOYEES]))
        .order_by(models.Notice.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notices


@router.post("/", response_model=schemas.NoticeResponse, status_code=status.HTTP_201_CREATED)
def create_notice(
    notice: schemas.NoticeCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    if notice.department.value != "all_employees" and notice.department != current_user.department:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create notices for your own department or the whole company",
        )
    new_notice = models.Notice(
        title=notice.title,
        content=notice.content,
        department=notice.department,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    return new_notice


@router.put("/{notice_id}", response_model=schemas.NoticeResponse)
def update_notice(
    notice_id: int,
    notice_update: schemas.NoticeUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    notice = db.query(models.Notice).filter(models.Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    if notice.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own notices")

    update_data = notice_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notice, field, value)
    notice.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(notice)
    return notice


@router.delete("/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notice(
    notice_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    notice = db.query(models.Notice).filter(models.Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    if notice.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own notices")
    db.delete(notice)
    db.commit()
    return None