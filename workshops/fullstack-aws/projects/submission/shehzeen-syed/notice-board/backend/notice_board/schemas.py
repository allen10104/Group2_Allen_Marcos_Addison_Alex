"""
Pydantic request/response models shared across routers.

Validation lives here once (min/max lengths, email format) so route
handlers never have to check field shape themselves — FastAPI rejects
a malformed body with a 422 before the handler runs.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NoticeCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class NoticeUpdate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class NoticePinUpdate(BaseModel):
    pinned: bool
