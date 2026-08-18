from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from models import Department
from datetime import datetime
from pydantic import ConfigDict, BaseModel, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Plain-text password, hashed before storage")
    department: Department = Field(..., description="The employee's own department")

    @field_validator("department")
    @classmethod
    def department_must_be_real(cls, value: Department) -> Department:
        if value == Department.ALL_EMPLOYEES:
            raise ValueError("'all_employees' is not a valid personal department")
        return value


class NoticeOwner(BaseModel):
    username: str
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    department: Department



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class NoticeCreate(BaseModel):
    title: str = Field(..., description="The title of the notice")
    content: str = Field(..., description="The content of the notice")
    department: Department = Field(..., description="Who this notice is tagged for")


class NoticeUpdate(BaseModel):
    title: Optional[str] = Field(None, description="The title of the notice")
    content: Optional[str] = Field(None, description="The content of the notice")
    department: Optional[Department] = Field(None, description="Who this notice is tagged for")


class NoticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="The unique identifier of the notice")
    title: str = Field(..., description="The title of the notice")
    content: str = Field(..., description="The content of the notice")
    department: Department = Field(..., description="Who this notice is tagged for")
    owner_id: int = Field(..., description="The user who created this notice")
    owner: NoticeOwner = Field(..., description="The user who created this notice")
    created_at: datetime = Field(..., description="The creation timestamp of the notice")
    updated_at: datetime = Field(..., description="The last update timestamp of the notice")

