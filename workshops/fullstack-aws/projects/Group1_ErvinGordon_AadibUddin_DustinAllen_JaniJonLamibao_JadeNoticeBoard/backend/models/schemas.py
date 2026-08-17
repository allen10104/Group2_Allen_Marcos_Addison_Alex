from datetime import datetime
from typing import Optional
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class User_Create(BaseModel):
    password: str
    email: str

class User_Out(BaseModel):
    id: UUID
    email: str
    created_at: datetime

class token(BaseModel):
    access_token: str
    token_type: str

class notice_Create(BaseModel):
    message: str
    is_pinned: bool = False
    expires_in_days: Optional[float] = None

class notice_Out(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    message: str
    is_pinned: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime

class notice_Pin(BaseModel):
    is_pinned: bool