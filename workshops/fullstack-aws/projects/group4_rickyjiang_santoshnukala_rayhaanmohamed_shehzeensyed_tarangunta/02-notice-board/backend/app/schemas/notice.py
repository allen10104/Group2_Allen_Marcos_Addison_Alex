"""API request/response models.

WHY SEPARATE FROM THE DOMAIN? If you return the `Notice` dataclass straight from a
route you couple your HTTP contract to your storage model — rename a field for Mongo
and you silently break the frontend. Worse, on Employee you'd serialise password_hash
to the browser. These schemas are the seam.

Pydantic also gives you validation and OpenAPI docs for free from the same declaration.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import Category, NoticeStatus, Priority
from app.domain.notice import Notice


class NoticeCreate(BaseModel):
    """What the client sends when creating or updating a notice.

    This is the OUTER wall — bad input is rejected as a 422 with field-level detail
    before a single line of business code runs. Notice.create() is the INNER wall for
    callers that bypass HTTP. Two walls, on purpose.

    Note what is NOT here: id, author, created_at, status. A client must not be able
    to set those. Accepting an `author` field from the request body would let anyone
    post a notice signed by the Chief Compliance Officer. It's designed out, not
    validated away.
    """

    title: str = Field(min_length=1, max_length=140)
    body: str = Field(min_length=1, max_length=5000)

    # Enum-typed, so "URGNET" is rejected automatically with a clear message.
    category: Category = Category.GENERAL
    priority: Priority = Priority.NORMAL

    department: str | None = Field(default=None, max_length=60)
    expires_at: datetime | None = None

    @field_validator("title", "body")
    @classmethod
    def not_blank(cls, v: str) -> str:
        """min_length=1 permits "   ". Strip first, then reject.

        A title of three spaces passes a naive length check and then renders as an
        empty card in the UI — the kind of bug that survives to production because
        nobody tests whitespace."""
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class NoticeResponse(BaseModel):
    """What the API sends back.

    Separate from NoticeCreate because the shapes genuinely differ — this one carries
    server-owned fields the client can't set, plus derived display fields so the React
    app doesn't need its own copy of the enum-to-label mapping.
    """

    id: str
    title: str
    body: str
    category: Category
    category_label: str
    priority: Priority
    escalated: bool
    department: str | None
    author_employee_id: str
    author_name: str | None
    pinned: bool
    status: NoticeStatus
    acknowledgement_required: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, n: Notice) -> "NoticeResponse":
        """Entity -> DTO mapping, hand-written on purpose.

        It's 18 lines with zero runtime magic, and when a field is wrong you can see
        why by reading it. Automatic mappers are where an afternoon disappears."""
        return cls(
            id=n.id or "",
            title=n.title,
            body=n.body,
            category=n.category,
            category_label=n.category.display_name,
            priority=n.priority,
            escalated=n.priority.escalated,
            department=n.department,
            author_employee_id=n.author_employee_id,
            author_name=n.author_name,
            pinned=n.pinned,
            status=n.status,
            acknowledgement_required=n.category.acknowledgement_required,
            expires_at=n.expires_at,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
    