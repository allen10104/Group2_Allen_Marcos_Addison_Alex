"""
Business logic for user service
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import FollowORM, UserORM
from app.models.exceptions import UserNotFoundException, ValidationException

def list_users(db: Session):
    """
    List all users in the database.
    """
    query = select(UserORM).where(UserORM.user_id != current_user_id)
    if search:
        query = query.where(UserORM.email.ilike(f"%{search}%"))
    query = query.order_by(UserORM.email.asc())
    return db.execute(query).scalars().all()

def list_followed_users(db: Session, user_id: str):
    """
    List all users that the given user is following.
    """
    query = (
        select(UserORM)
        .join(FollowORM, FollowORM.followed_id == UserORM.user_id)
        .where(FollowORM.follower_id == user_id)
        .order_by(UserORM.email.asc())
    )
    return db.execute(query).scalars().all()

def list_followers(db: Session, user_id: str):
    """
    List all users that are following the given user.
    """
    query = (
        select(UserORM)
        .join(FollowORM, FollowORM.follower_id == UserORM.user_id)
        .where(FollowORM.followed_id == user_id)
        .order_by(UserORM.email.asc())
    )
    return db.execute(query).scalars().all()

def follow_user(db: Session, follower_id: str, followed_id: str):
    """
    Follow a user.
    """
    if follower_id == followed_id:
        raise ValidationException("You cannot follow yourself.")

    # Check if the followed user exists
    followed_user = db.get(UserORM, followed_id)
    if not followed_user:
        raise UserNotFoundException(f"User with ID {followed_id} not found.")

    # Check if the follow relationship already exists
    existing_follow = (
        db.query(FollowORM)
        .filter(FollowORM.follower_id == follower_id, FollowORM.followed_id == followed_id)
        .first()
    )
    if existing_follow:
        raise ValidationException("You are already following this user.")

    # Create the follow relationship
    new_follow = FollowORM(follower_id=follower_id, followed_id=followed_id)
    db.add(new_follow)
    db.commit()

def unfollow_user(db: Session, follower_id: str, followed_id: str):
    """
    Unfollow a user.
    """
    follow = (
        db.query(FollowORM)
        .filter(FollowORM.follower_id == follower_id, FollowORM.followed_id == followed_id)
        .first()
    )
    if not follow:
        raise ValidationException("You are not following this user.")

    db.delete(follow)
    db.commit()

