# Column defines a table column with a specific data type.
from sqlalchemy import Column, Integer, String

from backend.database.base import Base


# Organization represents one company/team using the Notice Board.
# Every User and every Notice belongs to exactly one Organization.
class Organization(Base):
    __tablename__ = "organizations"

    # Primary key — PostgreSQL auto-assigns and increments this.
    id = Column(Integer, primary_key=True)

    # The organization's display name, e.g. "Acme Corp".
    name = Column(String(120), nullable=False)

    # The single code shared with members to join THIS specific
    # organization's board. unique=True means no two organizations can
    # ever end up with the same code.
    org_code = Column(String(12), unique=True, nullable=False)

    # Custom constructor so we can write Organization(name, org_code)
    # instead of naming every argument.
    def __init__(self, name: str, org_code: str, **kwargs):
        super().__init__(name=name, org_code=org_code, **kwargs)