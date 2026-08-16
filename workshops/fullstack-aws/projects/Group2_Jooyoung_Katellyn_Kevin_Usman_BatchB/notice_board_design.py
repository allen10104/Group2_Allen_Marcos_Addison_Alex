from enum import Enum


class Category(Enum):
    ANNOUNCEMENT = "Announcement"
    EVENT = "Event"
    GENERAL = "General"
    OTHER = "Other"


class Notice:
    MAX_CONTENT_LENGTH = 500

    def __init__(self, id, title, date, content, category):
        self.validate(title, content, category)
        self.id = id
        self.title = title.strip()
        self.date = date
        self.content = content.strip()
        self.category = category
        # Stamped by NoticeBoard.add_notice from the actor. Do not set these yourself.
        self.author = None
        self.author_id = None

    @staticmethod
    def validate(title, content, category):
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Title is required")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content is required")
        if len(content.strip()) > Notice.MAX_CONTENT_LENGTH:
            raise ValueError(f"Content must be at most {Notice.MAX_CONTENT_LENGTH} characters")
        if not isinstance(category, Category):
            raise ValueError("Category must be a Category")

    def __str__(self):
        return (
            f"[{self.id}] {self.title} by {self.author} "
            f"({self.date}): {self.content} [{self.category.value}]"
        )

    def __repr__(self):
        return (
            f"Notice(id={self.id}, title={self.title}, date={self.date}, "
            f"author={self.author}, author_id={self.author_id}, "
            f"content={self.content}, category={self.category})"
        )

    def __eq__(self, other):
        if not isinstance(other, Notice):
            return False
        return self.id == other.id


class NoticeBoard:
    # The board is the only store of notices. A user's history is a query
    # over this list (notices_by_author), not a second copy on User.
    def __init__(self, notices=None):
        self.notice_list = notices if notices is not None else []

    def find_by_id(self, notice_id):
        for notice in self.notice_list:
            if notice.id == notice_id:
                return notice
        return None

    def add_notice(self, notice, actor):
        if self.find_by_id(notice.id) is not None:
            raise ValueError("Notice id already exists")
        notice.author = actor.name
        notice.author_id = actor.id
        self.notice_list.append(notice)

    def remove_notice(self, notice_id, actor):
        existing = self.find_by_id(notice_id)
        if existing is None:
            raise ValueError("Notice not found")
        if not actor.can_modify(existing):
            raise ValueError("You are not authorized to remove this notice")
        self.notice_list.remove(existing)

    def edit_notice(self, notice_id, actor, **updates):
        existing = self.find_by_id(notice_id)
        if existing is None:
            raise ValueError("Notice not found")
        if not actor.can_modify(existing):
            raise ValueError("You are not authorized to edit this notice")

        allowed = {"title", "date", "content", "category"}
        unknown = set(updates) - allowed
        if unknown:
            raise ValueError(f"Cannot update fields: {sorted(unknown)}")

        title = updates.get("title", existing.title)
        date = updates.get("date", existing.date)
        content = updates.get("content", existing.content)
        category = updates.get("category", existing.category)
        Notice.validate(title, content, category)

        existing.title = title.strip()
        existing.date = date
        existing.content = content.strip()
        existing.category = category

    def get_all_notices(self):
        return list(self.notice_list)

    def notices_by_author(self, author_id):
        return [notice for notice in self.notice_list if notice.author_id == author_id]


class User:
    def __init__(self, id, name, email, password, is_admin=False):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def can_modify(self, notice):
        return notice.author_id == self.id or self.is_admin

    def my_notices(self, board):
        return board.notices_by_author(self.id)
