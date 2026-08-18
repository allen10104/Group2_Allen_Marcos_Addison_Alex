# Session is the type hint for the database session object.
from sqlalchemy.orm import Session

# Import the Like class so we can query and create rows through it.
from backend.models.like import Like


# Finds an existing like by a specific user on a specific notice or comment.
# Only one of notice_id/comment_id should be passed at a time, matching
# how the Like model itself works. Returns None if no like exists yet.
def get_like(db: Session, user_id: int, notice_id: int = None, comment_id: int = None):
    # Start the query filtered to this user's likes.
    query = db.query(Like).filter(Like.user_id == user_id)

    # Narrow further to a specific notice, if one was given.
    if notice_id is not None:
        query = query.filter(Like.notice_id == notice_id)

    # Narrow further to a specific comment, if one was given.
    if comment_id is not None:
        query = query.filter(Like.comment_id == comment_id)

    # Return the single matching row, or None if there isn't one.
    return query.first()


# Adds a new like for a user on a notice or comment.
# Assumes the caller already checked no like exists yet (done in the
# controller, to avoid duplicate likes).
def add_like(db: Session, user_id: int, notice_id: int = None, comment_id: int = None):
    # Build the Python object in memory first — nothing is saved yet.
    new_like = Like(user_id, notice_id, comment_id)

    # Stage the new object to be inserted.
    db.add(new_like)
    # Actually write it to PostgreSQL.
    db.commit()
    # Reload the object so it picks up the id PostgreSQL generated.
    db.refresh(new_like)

    return new_like


# Removes a user's like from a notice or comment (this is the "unlike"
# action). Returns True if a like was found and removed, False if the
# user hadn't liked it in the first place.
def remove_like(db: Session, user_id: int, notice_id: int = None, comment_id: int = None):
    # Reuse get_like to find the exact row to delete.
    like = get_like(db, user_id, notice_id, comment_id)

    # Nothing to remove if the user never liked this.
    if like is None:
        return False

    # Stage the deletion.
    db.delete(like)
    # Commit it, actually removing the row from PostgreSQL.
    db.commit()

    return True


# Counts how many likes a notice or comment has. Used to display the
# like count in the response.
def count_likes(db: Session, notice_id: int = None, comment_id: int = None):
    # Start with every like.
    query = db.query(Like)

    # Narrow to a specific notice, if given.
    if notice_id is not None:
        query = query.filter(Like.notice_id == notice_id)

    # Narrow to a specific comment, if given.
    if comment_id is not None:
        query = query.filter(Like.comment_id == comment_id)

    # .count() runs a SQL COUNT instead of loading every row into Python.
    return query.count()