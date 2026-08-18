# Column defines a table column with a specific data type.
# Integer, String, DateTime are the SQL types for each field below. ForeignKey links this table to another
# table's primary key (here, organizations.id).
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

# func gives access to SQL functions like now(), used below for created_at.
from sqlalchemy.sql import func

# Note: importing from "database"
from backend.database.base import Base


# Notice represents a single posted announcement on the board.
class Notice(Base):
    # __tablename__ tells SQLAlchemy what to call this table in PostgreSQL.
    __tablename__ = "notices"

    # Primary key column — PostgreSQL auto-assigns and increments this
    # for every new row, so we never set it manually.
    id = Column(Integer, primary_key=True)

    # Who posted the notice. nullable=False means PostgreSQL will reject
    # any row where this is left empty.
    name = Column(String(120), nullable=False)

    # The actual announcement text. Also required.
    message = Column(String(500), nullable=False)

    # server_default=func.now() means PostgreSQL stamps the time itself
    # when the row is inserted, so we never have to set it manually.
    created_at = Column(DateTime, server_default=func.now())

    # tracks how many times this notice has been viewed.
    # default=0 means every new notice starts at zero views.
    view_count = Column(Integer, default=0, nullable=False)

    # Which organization's board this notice belongs to. This is what
    # makes members only ever see their own organization's notices.
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Custom constructor so we can write Notice("Alice", "Meeting at 3pm")
    # instead of having to name every argument. **kwargs lets extra fields
    # (like id, if ever needed) still get passed through to the base class.
    # Constructor now also requires organization_id.

    def __init__(self, name: str, message: str, organization_id: int, **kwargs):
        # super().__init__() is SQLAlchemy's own constructor — this is what
        # actually assigns the values to the row's columns.
        super().__init__(name=name, message=message, organization_id=organization_id, **kwargs)