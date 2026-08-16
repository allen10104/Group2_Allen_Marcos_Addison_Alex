from datetime import datetime

from pydantic import BaseModel

from backend.models.category import Category
from backend.models.notice import Notice


class NoticeCreateSchema(BaseModel):
    title: str
    content: str
    category: Category
    date: datetime | None = None


class NoticeUpdateSchema(BaseModel):
    title: str | None = None
    content: str | None = None
    category: Category | None = None
    date: datetime | None = None


class NoticeOutSchema(BaseModel):
    id: int
    title: str
    content: str
    category: str
    date: str
    author: str
    author_id: int

# Utility function to map domain Notice → HTTP response schema.
# used in the controllers to convert the domain model to the HTTP response schema.
def notice_to_out(notice: Notice) -> NoticeOutSchema:
    """Map domain Notice → HTTP response schema."""
    return NoticeOutSchema(
        id=notice.id,
        title=notice.title,
        content=notice.content,
        category=notice.category.value if isinstance(notice.category, Category) else str(notice.category),
        date=str(notice.date),
        author=notice.author or "",
        author_id=notice.author_id if notice.author_id is not None else 0,
    )
