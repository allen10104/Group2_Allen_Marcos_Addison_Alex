"""
Pytest fixtures for Notice Board backend unit tests.

Env vars are set before backend imports so JWT secrets and the in-memory
repo take effect (see NOTICE_BOARD_REPO=memory).
"""

from __future__ import annotations

import os

# Must run before importing backend modules that read env at import time.
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters!!"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
os.environ["NOTICE_BOARD_REPO"] = "memory"

import pytest
from fastapi.testclient import TestClient

from backend.auth.passwords import hash_password
from backend.main import app
from backend.models.category import Category
from backend.models.notice import Notice
from backend.models.user import User
from backend.repositories.notice_repository import InMemoryNoticeRepository
from backend.services import notice_service as notice_service_module
from backend.services.notice_service import NoticeService


@pytest.fixture
def alice() -> User:
    return User(
        id=10,
        name="Alice",
        email="alice@example.com",
        password_hash=hash_password("password"),
        is_admin=False,
    )


@pytest.fixture
def bob() -> User:
    return User(
        id=20,
        name="Bob",
        email="bob@example.com",
        password_hash=hash_password("password"),
        is_admin=False,
    )


@pytest.fixture
def admin() -> User:
    return User(
        id=99,
        name="Admin",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        is_admin=True,
    )


@pytest.fixture
def repo() -> InMemoryNoticeRepository:
    return InMemoryNoticeRepository()


@pytest.fixture
def service(repo: InMemoryNoticeRepository) -> NoticeService:
    """Fresh service per test — never use a shared Postgres singleton."""
    return NoticeService(repo)


@pytest.fixture
def sample_notice() -> Notice:
    notice = Notice(
        id=1,
        title="Welcome",
        date="2026-08-16",
        content="Hello everyone",
        category=Category.ANNOUNCEMENT,
    )
    notice.author = "Alice"
    notice.author_id = 10
    return notice


@pytest.fixture
def client():
    """
    HTTP client against the FastAPI app.
    NOTICE_BOARD_REPO=memory is set above so routes use in-memory storage.
    Reset the shared in-memory list between tests.
    """
    service = notice_service_module.notice_service
    service.notice_repository._notices.clear()
    service.notice_repository._next_id = 1
    with TestClient(app) as test_client:
        yield test_client
    service.notice_repository._notices.clear()
    service.notice_repository._next_id = 1
