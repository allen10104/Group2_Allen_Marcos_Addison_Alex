"""Service-layer tests: business rules against a real in-memory repository."""

import pytest

from app.domain.enums import Category, NoticeStatus, Priority
from app.errors import AccessDeniedError, NoticeNotFoundError


def test_publish_persists(service, notice_repo):
    result = service.publish(
        title="ATM skimming devices found downtown",
        body="Inspect all card readers before opening.",
        author_employee_id="E10001",
        category=Category.SECURITY_ALERT,
        priority=Priority.URGENT,
    )
    assert result.id is not None                 # storage assigned identity
    # Asserting the return value alone would still pass if the service forgot to
    # persist. Checking the repository proves the write happened.
    assert len(notice_repo.find_all()) == 1


def test_publish_escalates_low_priority_compliance(service):
    result = service.publish(
        title="AML refresher due Sept 30", body="Mandatory for client-facing staff.",
        author_employee_id="E10001",
        category=Category.COMPLIANCE, priority=Priority.LOW,   # LOW on compliance
    )
    assert result.priority == Priority.HIGH


def test_publish_leaves_ordinary_categories_alone(service):
    result = service.publish(
        title="Dress code", body="Business casual Mon-Thu.",
        author_employee_id="E10003", category=Category.HR, priority=Priority.LOW,
    )
    assert result.priority == Priority.LOW


def test_publish_rejects_invalid_input(service, notice_repo):
    with pytest.raises(ValueError):
        service.publish(title="", body="Body", author_employee_id="E1")
    # Nothing was persisted - the kind of bug that writes garbage rows to production.
    assert notice_repo.find_all() == []


def test_get_by_id_raises_when_missing(service):
    with pytest.raises(NoticeNotFoundError, match="nope"):
        service.get_by_id("nope")


def test_any_employee_may_archive(service, notice_repo):
    """Permissions are flat: E99999 did not write this and archives it anyway.

    This test documents the decision - without it, a reader cannot tell whether
    cross-user archiving is intended or an oversight."""
    n = service.publish("Some notice", "Body", author_employee_id="E10001")
    service.archive(n.id, acting_employee_id="E99999")

    assert notice_repo.find_by_id(n.id).status == NoticeStatus.ARCHIVED
    # And it is gone from the board - the acceptance criterion.
    assert notice_repo.find_board() == []


def test_archive_refuses_unidentified_caller(service):
    """The checkpoint is not decorative - it still demands a known actor."""
    n = service.publish("Some notice", "Body", author_employee_id="E10001")
    with pytest.raises(AccessDeniedError):
        service.archive(n.id, acting_employee_id="")
    assert n.status == NoticeStatus.ACTIVE


def test_board_ordering(service):
    """Pinned first, then priority descending, then newest."""
    low = service.publish("Low", "b", author_employee_id="E1", priority=Priority.LOW)
    service.publish("Urgent", "b", author_employee_id="E1", priority=Priority.URGENT)
    service.publish("Normal", "b", author_employee_id="E1", priority=Priority.NORMAL)
    service.set_pinned(low.id, True)

    # The pinned LOW notice outranks the URGENT one - that is what pinning means.
    assert [n.title for n in service.get_board()] == ["Low", "Urgent", "Normal"]
    