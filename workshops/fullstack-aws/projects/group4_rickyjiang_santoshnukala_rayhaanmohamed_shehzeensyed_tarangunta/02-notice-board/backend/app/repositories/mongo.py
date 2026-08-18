"""MongoDB implementations of the Phase 1 ports.

These are ADAPTERS: they implement the application's abstract repositories using
PyMongo. Nothing above this file knows MongoDB exists — that's the entire payoff for
having written base.py before writing any storage code.
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING

from app.domain.employee import Employee
from app.domain.enums import Category, NoticeStatus, Priority, Role
from app.domain.notice import Notice
from app.repositories.base import EmployeeRepository, NoticeRepository
from app.repositories.mongo_client import get_database


def _as_aware(dt: datetime | None) -> datetime | None:
    """Belt-and-braces on top of tz_aware=True.

    If a document was written by another tool without a zone, this stops a naive
    datetime leaking into the domain and detonating a comparison later."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class MongoNoticeRepository(NoticeRepository):

    COLLECTION = "notices"

    def __init__(self) -> None:
        self._col = get_database()[self.COLLECTION]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create indexes at startup if they don't already exist (idempotent).

        The board query filters on status, category and department. An unindexed
        filter is a COLLSCAN — Mongo reads every document in the collection. Fine at
        4 notices, miserable at 50,000. Indexing the fields you filter on is the
        single highest-value database habit there is."""
        self._col.create_index([("status", ASCENDING)])
        self._col.create_index([("category", ASCENDING)])
        self._col.create_index([("department", ASCENDING)])
        # Compound index matching the board's sort order.
        self._col.create_index([("pinned", DESCENDING), ("created_at", DESCENDING)])

    # ------------------------------------------------------------------
    # Mapping: domain object <-> BSON document
    # ------------------------------------------------------------------
    # Hand-written on purpose. It's 20 lines, it has no runtime magic, and it's the
    # ONLY place that knows the storage field names. Rename a column here and nothing
    # above this file changes.

    @staticmethod
    def _to_document(n: Notice) -> dict:
        return {
            "title": n.title,
            "body": n.body,
            # Category is a `str` Enum, so this stores as a plain BSON string and the
            # collection stays human-readable in the Atlas UI. That str mixin from
            # Phase 1 is doing real work here.
            "category": n.category.value,
            "priority": n.priority.value,
            "department": n.department,
            "author_employee_id": n.author_employee_id,
            "author_name": n.author_name,
            "pinned": n.pinned,
            "status": n.status.value,
            "expires_at": n.expires_at,
            "created_at": n.created_at,
            "updated_at": n.updated_at,
        }

    @staticmethod
    def _from_document(doc: dict) -> Notice:
        return Notice(
            # Mongo's _id is an ObjectId. The domain and the API only ever deal in
            # strings, so the conversion happens here at the boundary and nowhere else.
            id=str(doc["_id"]),
            title=doc["title"],
            body=doc["body"],
            category=Category(doc["category"]),
            priority=Priority(doc["priority"]),
            department=doc.get("department"),
            author_employee_id=doc["author_employee_id"],
            author_name=doc.get("author_name"),
            pinned=doc.get("pinned", False),
            status=NoticeStatus(doc.get("status", "ACTIVE")),
            expires_at=_as_aware(doc.get("expires_at")),
            created_at=_as_aware(doc["created_at"]),
            updated_at=_as_aware(doc["updated_at"]),
        )

    # ------------------------------------------------------------------
    # The port
    # ------------------------------------------------------------------

    def save(self, notice: Notice) -> Notice:
        doc = self._to_document(notice)

        if notice.id is None:
            result = self._col.insert_one(doc)
            # Mongo assigned the identity; hand it back to the domain object.
            notice.id = str(result.inserted_id)
        else:
            self._col.replace_one({"_id": ObjectId(notice.id)}, doc, upsert=True)

        return notice

    def find_by_id(self, notice_id: str) -> Notice | None:
        try:
            oid = ObjectId(notice_id)
        except (InvalidId, TypeError):
            # A malformed id is "not found", not a 500. Without this catch, hitting
            # /api/notices/banana raises InvalidId and the user gets a server error
            # for what is plainly a client mistake.
            return None

        doc = self._col.find_one({"_id": oid})
        return self._from_document(doc) if doc else None

    def find_board(
        self, category: Category | None = None, department: str | None = None
    ) -> list[Notice]:
        # Push as much filtering into the query as possible, so Mongo does the work
        # rather than shipping the whole collection to Python.
        query: dict = {"status": NoticeStatus.ACTIVE.value}
        if category is not None:
            query["category"] = category.value

        # NOTE: department is deliberately NOT in the query. A departmental filter
        # would exclude bank-wide notices (department is None), which every employee
        # must see. The clean fix is an $or clause; here we widen and let the domain's
        # is_visible_to() decide, which keeps ONE definition of visibility shared with
        # the in-memory repo. Correctness over index efficiency — and being able to
        # say "here's the $or I'd write with more time" is a good review answer.

        docs = [self._from_document(d) for d in self._col.find(query)]

        results = [
            n for n in docs
            # Expiry is time-relative, so it can't be a stored predicate without
            # recomputing on every read. is_live() asks the domain object.
            if n.is_live() and (department is None or n.is_visible_to(department))
        ]
        # Identical ordering to the in-memory repository — the API contract does not
        # change just because storage did.
        return sorted(results, key=lambda n: n.sort_key())

    def find_all(self) -> list[Notice]:
        return [self._from_document(d) for d in self._col.find({})]

    def delete_by_id(self, notice_id: str) -> None:
        try:
            self._col.delete_one({"_id": ObjectId(notice_id)})
        except (InvalidId, TypeError):
            pass


class MongoEmployeeRepository(EmployeeRepository):

    COLLECTION = "employees"

    def __init__(self) -> None:
        self._col = get_database()[self.COLLECTION]
        # unique=True is enforced by the DATABASE, not just by an application check.
        # An app-level "does this username exist?" test races under concurrency; a
        # unique index cannot.
        self._col.create_index([("username", ASCENDING)], unique=True)
        self._col.create_index([("employee_id", ASCENDING)], unique=True)

    @staticmethod
    def _to_document(e: Employee) -> dict:
        return {
            "employee_id": e.employee_id,
            "username": e.username,
            "password_hash": e.password_hash,
            "full_name": e.full_name,
            "department": e.department,
            # A set isn't BSON-serialisable — store a sorted list for stable documents.
            "roles": sorted(r.value for r in e.roles),
            "enabled": e.enabled,
            "created_at": e.created_at,
            "updated_at": e.updated_at,
        }

    @staticmethod
    def _from_document(doc: dict) -> Employee:
        return Employee(
            id=str(doc["_id"]),
            employee_id=doc["employee_id"],
            username=doc["username"],
            password_hash=doc["password_hash"],
            full_name=doc["full_name"],
            department=doc.get("department"),
            roles={Role(r) for r in doc.get("roles", ["EMPLOYEE"])},
            enabled=doc.get("enabled", True),
            created_at=_as_aware(doc["created_at"]),
            updated_at=_as_aware(doc["updated_at"]),
        )

    def save(self, employee: Employee) -> Employee:
        doc = self._to_document(employee)
        if employee.id is None:
            employee.id = str(self._col.insert_one(doc).inserted_id)
        else:
            self._col.replace_one({"_id": ObjectId(employee.id)}, doc, upsert=True)
        return employee

    def find_by_username(self, username: str) -> Employee | None:
        if not username:
            return None
        # Normalise here too: Employee.create() lowercases on the way in, so a lookup
        # for "P.Raman" must be lowercased on the way out or it never matches.
        doc = self._col.find_one({"username": username.strip().lower()})
        return self._from_document(doc) if doc else None

    def find_by_id(self, employee_id: str) -> Employee | None:
        try:
            doc = self._col.find_one({"_id": ObjectId(employee_id)})
        except (InvalidId, TypeError):
            return None
        return self._from_document(doc) if doc else None

    def count(self) -> int:
        return self._col.count_documents({})
    