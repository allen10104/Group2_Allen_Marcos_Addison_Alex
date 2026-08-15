""" Route handlers for user-related operations. """

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import UserORM, get_db
from app.security.dependencies import get_current_user
from app.services import userService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
def list_users(search: str | None = None, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    """
    List all users in the database, optionally filtered by a search term.
    """
    users = userService.list_users(db, current_user.user_id, search)
    return [u.to_dict() for u in users]

@router.get("/{user_id}/following")
def list_followed_users(user_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    """
    List all users that the given user is following.
    """
    users = userService.list_followed_users(db, user_id)
    return [u.to_dict() for u in users]

@router.get("/{user_id}/followers")
def list_followers(user_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    """
    List all users that are following the given user.
    """
    users = userService.list_followers(db, user_id)
    return [u.to_dict() for u in users]

@router.post("/{user_id}/follow", status_code=204)
def follow_user(user_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    """
    Follow a user.
    """
    userService.follow_user(db, current_user.user_id, user_id)

@router.delete("/{user_id}/unfollow", status_code=204)
def unfollow_user(user_id: str, db: Session = Depends(get_db), current_user: UserORM = Depends(get_current_user)):
    """
    Unfollow a user.
    """
    userService.unfollow_user(db, current_user.user_id, user_id)