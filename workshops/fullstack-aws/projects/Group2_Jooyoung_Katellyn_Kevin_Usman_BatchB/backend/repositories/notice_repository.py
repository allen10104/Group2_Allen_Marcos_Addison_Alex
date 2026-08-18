from backend.models.notice import Notice


class InMemoryNoticeRepository:
    """Storage only: save and load notices. No authorization or validation."""

    def __init__(self, notices=None):
        self._notices = list(notices) if notices is not None else []
        self._next_id = max((notice.id for notice in self._notices), default=0) + 1

    def next_id(self) -> int:
        notice_id = self._next_id
        self._next_id += 1
        return notice_id

    def list_all(self) -> list[Notice]:
        return list(self._notices)

    def get(self, notice_id: int) -> Notice | None:
        for notice in self._notices:
            if notice.id == notice_id:
                return notice
        return None

    def add(self, notice: Notice) -> None:
        self._notices.append(notice)

    def update(self, notice: Notice) -> None:
        # In-memory notices are mutated in place; nothing else to write.
        existing = self.get(notice.id)
        if existing is None:
            raise ValueError("Notice not found")

    def delete(self, notice_id: int) -> None:
        self._notices = [notice for notice in self._notices if notice.id != notice_id]
