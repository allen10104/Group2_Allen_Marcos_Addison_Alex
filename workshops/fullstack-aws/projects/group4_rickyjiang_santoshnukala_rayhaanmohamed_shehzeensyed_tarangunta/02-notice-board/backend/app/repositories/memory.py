"""Phase 2 storage: dictionaries that live in the process and vanish on restart."""

import uuid

from app.domain.employee import Employee
from app.domain.enums import Category
from app.domain.notice import Notice
from app.repositories.base import EmployeeRepository, NoticeRepository


class InMemoryNoticeRepository(NoticeRepository):
    """Implements the Phase 1 port with a plain dict.

    In Phase 3 the Mongo implementation replaces this and NOTHING ELSE CHANGES —
    not the service, not the routers, not the schemas. That's the payoff for
    declaring the abstract base class.
    """

    def __init__(self) -> None:
        self._store: dict[str, Notice] = {}

    def save(self, notice: Notice) -> Notice:
        # A brand-new Notice has no id. We generate one here because assigning
        # identity is storage's job — in Phase 3, MongoDB does exactly this for us.
        if notice.id is None:
            notice.id = str(uuid.uuid4())
        self._store[notice.id] = notice
        return notice

    def find_by_id(self, notice_id: str) -> Notice | None:
        return self._store.get(notice_id)

    def find_board(
        self, category: Category | None = None, department: str | None = None
    ) -> list[Notice]:
        results = [
            n
            for n in self._store.values()
            # is_live() is domain behaviour from Phase 1 — the repository asks the
            # Notice whether it belongs on the board rather than re-deriving it.
            if n.is_live()
            and (category is None or n.category == category)
            and (department is None or n.is_visible_to(department))
        ]
        # sort_key() also lives on the domain object, so the Mongo repository in
        # Phase 3 sorts identically by construction. The API contract does not change
        # just because storage did.
        return sorted(results, key=lambda n: n.sort_key())

    def find_all(self) -> list[Notice]:
        return list(self._store.values())

    def delete_by_id(self, notice_id: str) -> None:
        self._store.pop(notice_id, None)


class InMemoryEmployeeRepository(EmployeeRepository):
    def __init__(self) -> None:
        self._store: dict[str, Employee] = {}

    def save(self, employee: Employee) -> Employee:
        if employee.id is None:
            employee.id = str(uuid.uuid4())
        self._store[employee.id] = employee
        return employee

    def find_by_username(self, username: str) -> Employee | None:
        if not username:
            return None
        needle = username.strip().lower()
        return next((e for e in self._store.values() if e.username == needle), None)

    def find_by_id(self, employee_id: str) -> Employee | None:
        return self._store.get(employee_id)

    def count(self) -> int:
        return len(self._store)
    