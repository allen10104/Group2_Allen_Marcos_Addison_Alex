# Column defines a table column. ForeignKey links this table to another
# table's primary key (here, notices.id and users.id).
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

# func gives access to SQL functions like now(), used below for created_at.
from sqlalchemy.sql import func

from backend.database.base import Base


# Comment represents a single comment a user left under a notice.
class Comment(Base):
    __tablename__ = "comments"

    # Primary key column.
    id = Column(Integer, primary_key=True)

    # Which notice this comment belongs to. ForeignKey enforces that this
    # must match a real row in the notices table.
    notice_id = Column(Integer, ForeignKey("notices.id"), nullable=False)

    # Which user wrote this comment.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # The comment text itself.
    text = Column(String(1000), nullable=False)

    # When the comment was posted, stamped by PostgreSQL automatically.
    created_at = Column(DateTime, server_default=func.now())

    # Custom constructor so we can write Comment(notice_id, user_id, text)
    # instead of naming every argument.
    def __init__(self, notice_id: int, user_id: int, text: str, **kwargs):
        super().__init__(notice_id=notice_id, user_id=user_id, text=text, **kwargs)