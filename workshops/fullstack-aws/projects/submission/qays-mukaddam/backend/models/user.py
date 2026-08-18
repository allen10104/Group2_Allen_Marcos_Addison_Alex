# Column defines a table column. ForeignKey links this table to another
# table's primary key (here, organizations.id).
from sqlalchemy import Column, Integer, String, ForeignKey

# Base is what every model inherits from, so SQLAlchemy knows this class
# maps to a real database table.
from backend.database.base import Base


# User represents anyone who can log in — either an organization's ADMIN
# (who posts notices) or a regular MEMBER (who can view, comment, and like).
class User(Base):
    # __tablename__ tells SQLAlchemy what to call this table in PostgreSQL.
    __tablename__ = "users"

    # Primary key — PostgreSQL auto-assigns and increments this.
    id = Column(Integer, primary_key=True)

    # Login name. unique=True means PostgreSQL rejects a second user with
    # the same username.
    username = Column(String(50), unique=True, nullable=False)

    # We never store the raw password — only its bcrypt hash, generated in
    # core/security.py before this gets saved.
    hashed_password = Column(String(255), nullable=False)

    # Either "ADMIN" or "MEMBER". Controls what the user is allowed to do,
    # checked in core/dependencies.py.
    role = Column(String(20), nullable=False, default="MEMBER")

    # Which organization this user belongs to. Every user must belong to
    # exactly one — nullable=False enforces that.
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Custom constructor so we can write User(username, hashed_pw, role, org_id)
    # instead of naming every argument.
    # Parameter order: username, hashed_password, role, organization_id.
    def __init__(self, username: str, hashed_password: str, role: str, organization_id: int, **kwargs):
        # super().__init__() is SQLAlchemy's own constructor — this is what
        # actually assigns the values to the row's columns.
        super().__init__(
            username=username,
            hashed_password=hashed_password,
            role=role,
            organization_id=organization_id,
            **kwargs
        )

    # Convenience method used by dependencies.py to check role-based access.
    def has_role(self, role_name: str) -> bool:
        return self.role == role_name