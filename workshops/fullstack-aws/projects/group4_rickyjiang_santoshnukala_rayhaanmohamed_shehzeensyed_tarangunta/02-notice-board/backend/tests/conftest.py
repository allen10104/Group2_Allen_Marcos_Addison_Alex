"""Pytest fixtures shared across the suite."""

import sys
from pathlib import Path

import pytest

# Put backend/ on the import path so `from app...` resolves when pytest runs from the
# project root.
BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.domain.enums import Category                 # noqa: E402
from app.domain.notice import Notice                  # noqa: E402
from app.repositories.memory import InMemoryNoticeRepository   # noqa: E402
from app.services.notice_service import NoticeService # noqa: E402


@pytest.fixture
def notice_repo() -> InMemoryNoticeRepository:
    """A fresh empty repository per test.

    This is why the in-memory implementation keeps earning its keep after Mongo
    arrives: it IS the test double. A real object with real behaviour, backed by a
    dict - usually better than a mock, because it cannot drift from the interface.
    """
    return InMemoryNoticeRepository()


@pytest.fixture
def service(notice_repo) -> NoticeService:
    """Constructed with `NoticeService(repo)` - no app startup, no database.
    Possible only because Phase 2 used constructor injection."""
    return NoticeService(notice_repo)


@pytest.fixture
def sample_notice() -> Notice:
    return Notice.create(
        title="Wire cutoff moved to 3:30 PM ET",
        body="Effective Monday, the same-day domestic wire cutoff moves earlier.",
        author_employee_id="E10001",
        author_name="Priya Raman",
        category=Category.OPERATIONS,
    )
