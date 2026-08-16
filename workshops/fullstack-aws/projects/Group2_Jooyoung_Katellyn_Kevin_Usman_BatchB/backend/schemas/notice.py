from pydantic import BaseModel
from backend.models.notice import Notice
from datetime import datetime

class NoticeCreateSchema(BaseModel):
    title: str
    content: str
    category: str
    date: datetime

class NoticeUpdateSchema(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    date: datetime | None = None

class NoticeOutSchema(BaseModel):
    id: int
    title: str
    content: str
    category: str
    date: datetime
    author: str
    author_id: int

