"""Request schemas -- the shape of an incoming request body.
 
No response schemas here: ORM models return their own shape via to_dict()
(see models/database.py) -- same convention as the rest of the codebase.
"""
 
from pydantic import BaseModel, EmailStr, Field
 
 
class RegisterRequest(BaseModel):
    """Body for POST /api/v1/auth/register."""
 
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
 
 
class LoginRequest(BaseModel):
    """Body for POST /api/v1/auth/login."""
 
    email: EmailStr
    password: str
 
 
class NoticeCreate(BaseModel):
    """Body for POST /api/v1/notices."""
 
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
 
 
class NoticeUpdate(BaseModel):
    """Body for PUT /api/v1/notices/{id}. All fields optional -- only
    supplied fields get changed."""
 
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)