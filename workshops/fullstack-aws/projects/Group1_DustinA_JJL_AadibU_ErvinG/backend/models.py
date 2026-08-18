import enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Department(str, enum.Enum):
    ACCOUNTING = "accounting"
    SECURITY = "security"
    HUMAN_RESOURCES = "human_resources"
    ALL_EMPLOYEES = "all_employees"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    department = Column(Enum(Department), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False)

    notices = relationship("Notice", back_populates="owner", cascade="all, delete-orphan")


class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    department = Column(Enum(Department), nullable=False, default=Department.ALL_EMPLOYEES)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    owner = relationship("User", back_populates="notices")