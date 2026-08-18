# APIRouter lets us define routes separately and plug them into main.py's app.
# HTTPException lets us return proper error responses.
# Depends is how FastAPI hands a database session or user into an endpoint.
from fastapi import APIRouter, HTTPException, Depends

# Session is the type hint for the database session object.
from sqlalchemy.orm import Session

# get_db opens a session for this request and closes it afterwards.
from backend.database.session import get_db

# Import the service functions that contain the actual like/unlike logic.
from backend.services.like_service import get_like, add_like, remove_like, count_likes

# get_current_user allows any logged-in user through. CurrentUser is the
# type hint for whoever the token identifies as.
from backend.core.dependencies import get_current_user, CurrentUser


# Create a router for like-related endpoints. main.py will register this
# with app.include_router(...).
router = APIRouter()


# POST /notices/{notice_id}/like
# Likes a notice as the currently logged-in user.
@router.post("/notices/{notice_id}/like", status_code=201)
def like_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Check whether this user already liked this notice, to avoid
    # duplicate likes.
    existing = get_like(db, current_user.user_id, notice_id=notice_id)

    # Reject if they already liked it once.
    if existing is not None:
        raise HTTPException(status_code=400, detail="You already liked this notice")

    # Create the like.
    add_like(db, current_user.user_id, notice_id=notice_id)

    # Return the updated total so the frontend can refresh the count
    # without a second request.
    return {"message": "Notice liked", "like_count": count_likes(db, notice_id=notice_id)}


# DELETE /notices/{notice_id}/like
# Removes the currently logged-in user's own like from a notice. This is
# the "members can remove a like" rule.
@router.delete("/notices/{notice_id}/like")
def unlike_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # remove_like only ever removes THIS user's own like, since it's
    # filtered by current_user.user_id — there's no way to unlike on
    # someone else's behalf.
    was_removed = remove_like(db, current_user.user_id, notice_id=notice_id)

    # Nothing to remove if they never liked it.
    if not was_removed:
        raise HTTPException(status_code=404, detail="You haven't liked this notice")

    return {"message": "Like removed", "like_count": count_likes(db, notice_id=notice_id)}


# POST /comments/{comment_id}/like
# Likes a comment as the currently logged-in user. Same pattern as
# liking a notice, just targeting a comment instead.
@router.post("/comments/{comment_id}/like", status_code=201)
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Check for an existing like from this user on this comment.
    existing = get_like(db, current_user.user_id, comment_id=comment_id)

    # Reject duplicate likes.
    if existing is not None:
        raise HTTPException(status_code=400, detail="You already liked this comment")

    # Create the like.
    add_like(db, current_user.user_id, comment_id=comment_id)

    return {"message": "Comment liked", "like_count": count_likes(db, comment_id=comment_id)}


# DELETE /comments/{comment_id}/like
# Removes the currently logged-in user's own like from a comment.
@router.delete("/comments/{comment_id}/like")
def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Only removes this user's own like on this comment.
    was_removed = remove_like(db, current_user.user_id, comment_id=comment_id)

    if not was_removed:
        raise HTTPException(status_code=404, detail="You haven't liked this comment")

    return {"message": "Like removed", "like_count": count_likes(db, comment_id=comment_id)}