from datetime import date
import os

from dotenv import load_dotenv

from backend.models.category import Category
from backend.models.notice import Notice
from backend.models.user import User

load_dotenv()


class NoticeService:
    """Use cases and rules: who may post/edit/delete, author stamping, search."""

    def __init__(self, notice_repository):
        self.notice_repository = notice_repository

    def list_notices(self, q=None, author=None, category=None, author_id=None) -> list[Notice]:
        notices = self.notice_repository.list_all()
        if author_id is not None:
            notices = [notice for notice in notices if notice.author_id == author_id]
        if author:
            needle = author.lower()
            notices = [
                notice for notice in notices
                if notice.author and needle in notice.author.lower()
            ]
        if category is not None:
            notices = [notice for notice in notices if notice.category == category]
        if q:
            needle = q.lower()
            notices = [
                notice for notice in notices
                if needle in notice.title.lower() or needle in notice.content.lower()
            ]
        return sorted(notices, key=lambda notice: notice.id, reverse=True)

    def get_notice(self, notice_id: int) -> Notice:
        notice = self.notice_repository.get(notice_id)
        if notice is None:
            raise ValueError("Notice not found")
        return notice

    def create_notice(self, title, content, category: Category, actor: User, notice_date=None) -> Notice:
        if notice_date is None:
            notice_date = date.today().isoformat()
        notice = Notice(
            id=self.notice_repository.next_id(),
            title=title,
            date=notice_date,
            content=content,
            category=category,
        )
        notice.author = actor.name
        notice.author_id = actor.id
        self.notice_repository.add(notice)
        return notice

    def update_notice(self, notice_id: int, actor: User, **updates) -> Notice:
        existing = self.get_notice(notice_id)
        if not actor.can_modify(existing):
            raise ValueError("You are not authorized to edit this notice")

        allowed = {"title", "date", "content", "category"}
        unknown = set(updates) - allowed
        if unknown:
            raise ValueError(f"Cannot update fields: {sorted(unknown)}")

        title = updates.get("title", existing.title)
        notice_date = updates.get("date", existing.date)
        content = updates.get("content", existing.content)
        category = updates.get("category", existing.category)
        Notice.validate(title, content, category)

        existing.title = title.strip()
        existing.date = notice_date
        existing.content = content.strip()
        existing.category = category
        self.notice_repository.update(existing)
        return existing

    def delete_notice(self, notice_id: int, actor: User) -> None:
        existing = self.get_notice(notice_id)
        if not actor.can_modify(existing):
            raise ValueError("You are not authorized to remove this notice")
        self.notice_repository.delete(notice_id)


def create_default_notice_service() -> NoticeService:
    """Postgres by default; set NOTICE_BOARD_REPO=memory for unit tests."""
    if os.getenv("NOTICE_BOARD_REPO", "postgres").lower() == "memory":
        from backend.repositories.notice_repository import InMemoryNoticeRepository

        return NoticeService(InMemoryNoticeRepository())

    from backend.repositories.postgres_notice_repository import PostgresNoticeRepository

    return NoticeService(PostgresNoticeRepository())


# Shared service for the process.
notice_service = create_default_notice_service()
