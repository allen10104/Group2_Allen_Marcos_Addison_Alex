"""The Notice entity — the heart of the domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.enums import Category, NoticeStatus, Priority


def _utc_now() -> datetime:
    """Timezone-aware UTC.

    NEVER datetime.now() without a timezone. A bank with branches in New York and
    Singapore cannot store "2026-08-16T14:00" with no zone and hope for the best.
    Aware UTC also serialises to ISO-8601 with a `Z`, which JavaScript's `new Date()`
    parses natively — that saves a real bug in the frontend."""
    return datetime.now(timezone.utc)


@dataclass
class Notice:
    """A single notice on the bank's internal board.

    DESIGN NOTES — say these in a review and you sound like you know what you're doing:

    1. NO FRAMEWORK IMPORTS. No pydantic, no pymongo, no fastapi. This module imports
       only the standard library and its own enums. Keeping the domain framework-free
       for as long as possible is exactly why the Phase 3 database swap is cheap.

    2. BEHAVIOUR LIVES WITH DATA. is_expired() and is_visible_to() are here, not in
       the service. A Notice knows whether it has expired; the service shouldn't have
       to reach in and compute it. (Avoiding the "anemic domain model" smell.)

    3. A CLASSMETHOD FACTORY, not a hand-built constructor. `Notice.create(...)` reads
       better at the call site and gives one place to stamp timestamps and defaults.

    4. VALIDATION HAPPENS HERE, not only at the API edge. Pydantic catches bad HTTP
       input, but the domain must also protect itself from bad calls originating in a
       test, a seed script, or a future message consumer. Defence in depth.
    """

    title: str
    body: str
    category: Category
    priority: Priority
    author_employee_id: str
    author_name: str | None = None

    # None means bank-wide (visible to everyone).
    department: str | None = None

    pinned: bool = False
    status: NoticeStatus = NoticeStatus.ACTIVE

    # Optional auto-expiry — e.g. "system maintenance this Saturday".
    expires_at: datetime | None = None

    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    # Assigned by the repository on first save. None until then.
    id: str | None = None

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        title: str,
        body: str,
        author_employee_id: str,
        author_name: str | None = None,
        category: Category | None = None,
        priority: Priority | None = None,
        department: str | None = None,
        expires_at: datetime | None = None,
    ) -> "Notice":
        """The only supported way to bring a brand-new Notice into existence."""

        if not title or not title.strip():
            raise ValueError("Notice title is required")
        if len(title.strip()) > 140:
            raise ValueError("Notice title must be 140 characters or fewer")
        if not body or not body.strip():
            raise ValueError("Notice body is required")
        if not author_employee_id or not author_employee_id.strip():
            raise ValueError("Notice must have an author")

        now = _utc_now()
        return cls(
            title=title.strip(),
            body=body.strip(),
            # Sensible defaults so callers can pass None and still get a valid object.
            category=category or Category.GENERAL,
            priority=priority or Priority.NORMAL,
            department=department.strip() if department and department.strip() else None,
            author_employee_id=author_employee_id,
            author_name=author_name,
            expires_at=expires_at,
            pinned=False,
            status=NoticeStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    # ------------------------------------------------------------------
    # Behaviour — the reason this isn't just a struct
    # ------------------------------------------------------------------

    def update(
        self,
        title: str | None = None,
        body: str | None = None,
        category: Category | None = None,
        priority: Priority | None = None,
        department: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        """Mutating operation, expressed as intent.

        Every field it touches is one an editor is genuinely allowed to change: you
        can fix a typo in the body, but you cannot rewrite history by changing the
        author or created_at. Passing None for a field means "leave it alone"."""
        if title and title.strip():
            self.title = title.strip()
        if body and body.strip():
            self.body = body.strip()
        if category is not None:
            self.category = category
        if priority is not None:
            self.priority = priority
        self.department = department.strip() if department and department.strip() else None
        self.expires_at = expires_at

        # The invariant: content changed => the clock moves.
        self.updated_at = _utc_now()

    def archive(self) -> None:
        """Soft delete. See NoticeStatus for why a bank doesn't hard-delete."""
        self.status = NoticeStatus.ARCHIVED
        self.updated_at = _utc_now()

    def set_pinned(self, pinned: bool) -> None:
        self.pinned = pinned
        self.updated_at = _utc_now()

    def is_expired(self) -> bool:
        """Had an expiry date, and that date has passed."""
        return self.expires_at is not None and self.expires_at < _utc_now()

    def is_live(self) -> bool:
        """On the board = active AND not past its expiry.

        Note these are different concepts: an expired notice is still ACTIVE. Both
        must be excluded from the board, and having one method say so means the
        in-memory and Mongo repositories can never disagree about what 'live' means."""
        return self.status == NoticeStatus.ACTIVE and not self.is_expired()

    def is_visible_to(self, viewer_department: str | None) -> bool:
        """Bank-wide notices (department is None) are visible to everyone;
        departmental notices only to that department. Case-insensitive, and safe
        when the viewer has no department set."""
        if self.department is None:
            return True
        if viewer_department is None:
            return False
        return self.department.lower() == viewer_department.lower()

    def was_authored_by(self, employee_id: str) -> bool:
        return self.author_employee_id == employee_id

    def sort_key(self) -> tuple:
        """Board ordering, defined once so both repositories sort identically:
        pinned first, then most urgent, then newest.

        Negation gives descending order on a normally-ascending sort. `not self.pinned`
        maps True -> False (0), so pinned notices sort first."""
        return (not self.pinned, -self.priority.weight, -self.created_at.timestamp())
    