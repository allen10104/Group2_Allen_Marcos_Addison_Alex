# Column defines a table column. ForeignKey links this table to another
# table's primary key (used below for user_id, notice_id, comment_id).
from sqlalchemy import Column, Integer, ForeignKey

# Base is what every model inherits from, so SQLAlchemy knows this class
# maps to a real database table.
from backend.database.base import Base


# Like represents one user liking either a notice OR a comment (never both
# at once). Exactly one of notice_id/comment_id will be set, the other
# stays None — that's why both are nullable.
class Like(Base):
    # __tablename__ tells SQLAlchemy what to call this table in PostgreSQL.
    __tablename__ = "likes"

    # Primary key column — PostgreSQL auto-assigns and increments this.
    id = Column(Integer, primary_key=True)

    # Which user made this like. Required on every row.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Set when this like is on a notice directly. None if it's a like on
    # a comment instead.
    notice_id = Column(Integer, ForeignKey("notices.id"), nullable=True)

    # Set when this like is on a comment. None if it's a like on a
    # notice instead.
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    # Custom constructor. notice_id/comment_id default to None so callers
    # only pass whichever one actually applies.
    def __init__(self, user_id: int, notice_id: int = None, comment_id: int = None, **kwargs):
        # super().__init__() is SQLAlchemy's own constructor — this is what
        # actually assigns the values to the row's columns.
        super().__init__(user_id=user_id, notice_id=notice_id, comment_id=comment_id, **kwargs)