"""The PORTS — the most important file in Phase 1.

These describe what the application needs from storage, in the application's own
vocabulary. Nothing about dicts, BSON, or connection strings appears here. Phase 2
implements them with a dict; Phase 3 implements them with MongoDB. The service layer
never knows or cares which is wired in.
"""

from abc import ABC, abstractmethod

from app.domain.employee import Employee
from app.domain.enums import Category
from app.domain.notice import Notice


class NoticeRepository(ABC):
    """Storage contract for notices."""

    @abstractmethod
    def save(self, notice: Notice) -> Notice:
        """Insert or update. Assigns `notice.id` on first save and returns the notice."""

    @abstractmethod
    def find_by_id(self, notice_id: str) -> Notice | None:
        """Returns None when absent.

        `Notice | None` in the signature is the type-checker's way of forcing the
        caller to think about the missing case — the Python equivalent of Optional."""

    @abstractmethod
    def find_board(
        self, category: Category | None = None, department: str | None = None
    ) -> list[Notice]:
        """The board query. Both filters optional (None = no filter).

        Returns only LIVE notices — archived and expired never reach the board —
        sorted pinned-first, then priority descending, then newest first."""

    @abstractmethod
    def find_all(self) -> list[Notice]:
        """Includes archived. Used by admin views and tests."""

    @abstractmethod
    def delete_by_id(self, notice_id: str) -> None:
        """Hard delete. The service archives instead; this exists for cleanup and tests."""


class EmployeeRepository(ABC):
    """Storage contract for staff. Phase 5's authentication is built on find_by_username."""

    @abstractmethod
    def save(self, employee: Employee) -> Employee: ...

    @abstractmethod
    def find_by_username(self, username: str) -> Employee | None: ...

    @abstractmethod
    def find_by_id(self, employee_id: str) -> Employee | None: ...

    @abstractmethod
    def count(self) -> int: ...
    