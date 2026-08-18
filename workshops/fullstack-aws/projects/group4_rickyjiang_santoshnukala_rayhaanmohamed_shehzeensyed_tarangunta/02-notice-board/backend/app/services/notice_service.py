"""Business rules for the notice board."""

import logging
from datetime import datetime

from app.domain.enums import Category, Priority
from app.domain.notice import Notice
from app.errors import AccessDeniedError, NoticeNotFoundError
from app.repositories.base import NoticeRepository

log = logging.getLogger(__name__)


class NoticeService:
    """Where the business rules live.

    CONSTRUCTOR INJECTION, not a module-level global repository. Three concrete reasons:
      1. Phase 4's tests do `NoticeService(FakeRepo())` with no database anywhere,
         turning a 4-second test into a 5-millisecond one.
      2. Swapping in-memory for Mongo is a wiring change, not a code change.
      3. The dependency is explicit — you can see what this class needs from its
         signature instead of grepping for imports.

    The declared type is the ABSTRACT NoticeRepository. This class has no idea it's
    currently talking to a dict, which is precisely the payoff from Phase 1.
    """

    def __init__(self, repository: NoticeRepository) -> None:
        self._repo = repository

    def publish(
        self,
        title: str,
        body: str,
        author_employee_id: str,
        author_name: str | None = None,
        category: Category | None = None,
        priority: Priority | None = None,
        department: str | None = None,
        expires_at: datetime | None = None,
    ) -> Notice:
        # Notice.create() does the validation. The service doesn't re-implement it —
        # one rule, one home.
        notice = Notice.create(
            title=title,
            body=body,
            author_employee_id=author_employee_id,
            author_name=author_name,
            category=category,
            priority=priority,
            department=department,
            expires_at=expires_at,
        )

        # A bank-realistic rule the domain can't decide alone: compliance and security
        # notices are never low priority, whatever the author selected.
        if notice.category.acknowledgement_required and notice.priority == Priority.LOW:
            notice.priority = Priority.HIGH
            log.info("Escalated LOW priority on an acknowledgement-required notice to HIGH")

        saved = self._repo.save(notice)
        # These log lines are what you'll grep in CloudWatch Logs Insights when
        # someone says "my notice didn't post".
        log.info(
            "Published notice id=%s category=%s priority=%s author=%s",
            saved.id, saved.category, saved.priority, author_employee_id,
        )
        return saved

    def get_by_id(self, notice_id: str) -> Notice:
        notice = self._repo.find_by_id(notice_id)
        if notice is None:
            # Raising a domain error turns "absent" into something the exception
            # handler maps to 404. No route ever writes an if-None check.
            raise NoticeNotFoundError(notice_id)
        return notice

    def get_board(
        self, category: Category | None = None, department: str | None = None
    ) -> list[Notice]:
        return self._repo.find_board(category, department)

    def update(
        self,
        notice_id: str,
        acting_employee_id: str,
        title: str | None = None,
        body: str | None = None,
        category: Category | None = None,
        priority: Priority | None = None,
        department: str | None = None,
        expires_at: datetime | None = None,
    ) -> Notice:
        notice = self.get_by_id(notice_id)
        self._assert_may_modify(notice, acting_employee_id)
        notice.update(title, body, category, priority, department, expires_at)
        return self._repo.save(notice)

    def archive(self, notice_id: str, acting_employee_id: str) -> None:
        notice = self.get_by_id(notice_id)
        self._assert_may_modify(notice, acting_employee_id)
        notice.archive()                      # soft delete — domain behaviour
        self._repo.save(notice)
        log.info("Archived notice id=%s by employee=%s", notice_id, acting_employee_id)

    def set_pinned(self, notice_id: str, pinned: bool) -> Notice:
        notice = self.get_by_id(notice_id)
        notice.set_pinned(pinned)
        return self._repo.save(notice)

    @staticmethod
    def _assert_may_modify(notice: Notice, acting_employee_id: str) -> None:
        """The one authorization checkpoint for modifying a notice.

        PERMISSIONS ARE FLAT: any authenticated employee may edit or archive any
        notice. So this currently only requires that we know WHO is acting — an
        unidentified caller is still refused, which keeps it from being decorative.

        It exists as a named method rather than being inlined because every mutation
        path routes through it, so tightening the rule later is an edit to THIS
        METHOD ONLY — no route changes, no risk of missing an endpoint. The commented
        line is the ownership rule a bank would actually want; being able to point at
        it is a better review answer than an empty method.

        In Phase 2 the routes pass a placeholder id. In Phase 5 it comes from the JWT
        and this starts doing real work — Phase 5 adds authentication only.
        """
        if not acting_employee_id or not acting_employee_id.strip():
            raise AccessDeniedError(
                f"An identified employee is required to modify notice {notice.id}"
            )
        

        