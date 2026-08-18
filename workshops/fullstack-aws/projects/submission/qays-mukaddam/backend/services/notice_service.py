# Session is the type hint for the database session object passed in from
# each controller function, via FastAPI's Depends(get_db).
from sqlalchemy.orm import Session

# Import the Notice class so we can query and create rows through it.
from backend.models.notice import Notice

# Import Comment and Like so delete_notice can clean up anything that
# references a notice before deleting it.
from backend.models.comment import Comment
from backend.models.like import Like


# Creates a new notice, tied to a specific organization.
# organization_id comes from the requester's own account, not from user
# input, so an admin can only ever post to their own org's board.
def create_notice(db: Session, name: str, message: str, organization_id: int):
    new_notice = Notice(name, message, organization_id)

    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)

    return new_notice


# Returns every notice belonging to a specific organization, most recent
# first. This is what makes members only ever see their own org's board.
def list_notices(db: Session, organization_id: int):
    return db.query(Notice).filter(Notice.organization_id == organization_id).order_by(Notice.id.desc()).all()


# Looks up a single notice by id AND organization_id, incrementing its
# view count. Requiring BOTH means a user can't view a notice from a
# different organization just by guessing/entering another id in the URL.
# Returns None if no matching notice exists in THIS organization.
def get_notice_by_id(db: Session, notice_id: int, organization_id: int):
    notice = db.query(Notice).filter(
        Notice.id == notice_id,
        Notice.organization_id == organization_id,
    ).first()

    if notice is None:
        return None

    notice.view_count += 1
    db.commit()
    db.refresh(notice)

    return notice


# Deletes a notice by id AND organization_id — same cross-org protection
# as get_notice_by_id. Also cleans up related likes and comments first,
# same as before.
def delete_notice(db: Session, notice_id: int, organization_id: int):
    notice = db.query(Notice).filter(
        Notice.id == notice_id,
        Notice.organization_id == organization_id,
    ).first()

    if notice is None:
        return False

    db.query(Like).filter(Like.notice_id == notice_id).delete()

    comment_ids = [c.id for c in db.query(Comment).filter(Comment.notice_id == notice_id).all()]

    if comment_ids:
        db.query(Like).filter(Like.comment_id.in_(comment_ids)).delete(synchronize_session=False)
        db.query(Comment).filter(Comment.notice_id == notice_id).delete()

    db.delete(notice)
    db.commit()

    return True

# Looks up a notice by id AND organization_id WITHOUT incrementing its
# view count. Used by other controllers (like comments) that just need
# to confirm a notice exists in the user's org, without that check
# itself counting as a "view".
def get_notice_for_org(db: Session, notice_id: int, organization_id: int):
    return db.query(Notice).filter(
        Notice.id == notice_id,
        Notice.organization_id == organization_id,
    ).first()