# Session is the type hint for the database session object passed in from
# each controller function, via FastAPI's Depends(get_db).
from sqlalchemy.orm import Session

# Import the Comment class so we can query and create rows through it.
from backend.models.comment import Comment

# Import Like so delete_comment can remove any likes on a comment
# before the comment itself gets deleted.
from backend.models.like import Like


# Creates a new comment under a notice.
# db is the database session. notice_id/user_id/text are the values to store.
def create_comment(db: Session, notice_id: int, user_id: int, text: str):
    # Build the Python object in memory first — nothing is saved yet.
    new_comment = Comment(notice_id, user_id, text)

    # Stage the new object to be inserted.
    db.add(new_comment)
    # Actually write it to PostgreSQL.
    db.commit()
    # Reload the object so it picks up the id and created_at that
    # PostgreSQL generated during the commit.
    db.refresh(new_comment)

    return new_comment


# Returns every comment on a given notice, oldest first (so a conversation
# reads top to bottom in the order it happened).
def list_comments_for_notice(db: Session, notice_id: int):
    # .filter narrows results to just this notice's comments.
    # .order_by(Comment.id.asc()) sorts lowest id (oldest) first.
    return db.query(Comment).filter(Comment.notice_id == notice_id).order_by(Comment.id.asc()).all()


# Looks up a single comment by id. Used by the controller to check who
# wrote it before allowing a delete.
def get_comment_by_id(db: Session, comment_id: int):
    # Query for a row matching this id, return the first match.
    return db.query(Comment).filter(Comment.id == comment_id).first()


# Deletes a comment by id, first removing any likes on it — without this,
# PostgreSQL's foreign key constraint would block the delete (a like
# can't point to a comment that no longer exists).
# Returns True if it worked, False if no comment had that id.
def delete_comment(db: Session, comment_id: int):
    # Look up the comment first — we need to confirm it exists.
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    # If nothing matched, there's nothing to delete.
    if comment is None:
        return False

    # Remove any likes on this comment first.
    db.query(Like).filter(Like.comment_id == comment_id).delete()

    # Now it's safe to delete the comment itself.
    db.delete(comment)
    # Commit both deletions as one transaction.
    db.commit()

    return True