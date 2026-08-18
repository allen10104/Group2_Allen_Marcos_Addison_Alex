"""Domain tests: no framework, no I/O, sub-millisecond."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.enums import Category, NoticeStatus, Priority, Role
from app.domain.notice import Notice


def _now():
    return datetime.now(timezone.utc)


def test_creates_with_defaults():
    n = Notice.create("Title", "Body text", "E10001")
    assert n.status == NoticeStatus.ACTIVE
    assert n.category == Category.GENERAL       # defaulted from None
    assert n.priority == Priority.NORMAL
    assert n.pinned is False
    # On creation both timestamps are the same instant - nothing has been edited yet.
    assert n.created_at == n.updated_at


def test_rejects_blank_title():
    # Asserting the MESSAGE, not just the type, proves the RIGHT validation fired.
    with pytest.raises(ValueError, match="title is required"):
        Notice.create("   ", "Body", "E10001")


def test_rejects_overlong_title():
    with pytest.raises(ValueError, match="140"):
        Notice.create("x" * 141, "Body", "E10001")


def test_rejects_missing_author():
    with pytest.raises(ValueError, match="author"):
        Notice.create("Title", "Body", "")


def test_archive_makes_not_live(sample_notice):
    assert sample_notice.is_live() is True
    sample_notice.archive()
    assert sample_notice.status == NoticeStatus.ARCHIVED
    assert sample_notice.is_live() is False


def test_expired_notice_is_not_live():
    n = Notice.create("Old window", "Body", "E10001",
                      expires_at=_now() - timedelta(days=1))
    assert n.is_expired() is True
    # Still ACTIVE - expiry and archival are different concepts, and the board must
    # exclude both. Easy to collapse by accident.
    assert n.status == NoticeStatus.ACTIVE
    assert n.is_live() is False


def test_update_moves_updated_at_but_not_created_at(sample_notice):
    before_updated = sample_notice.updated_at
    before_created = sample_notice.created_at

    sample_notice.update(title="Corrected title", priority=Priority.URGENT)

    assert sample_notice.title == "Corrected title"
    assert sample_notice.priority == Priority.URGENT
    # body=None meant "do not change it" - verify that contract holds.
    assert "wire cutoff" in sample_notice.body.lower()
    assert sample_notice.updated_at > before_updated
    # created_at must never move. History is not editable.
    assert sample_notice.created_at == before_created


def test_departmental_visibility_is_case_insensitive():
    n = Notice.create("Retail only", "Body", "E10001", department="RETAIL_BANKING")
    assert n.is_visible_to("RETAIL_BANKING") is True
    assert n.is_visible_to("retail_banking") is True
    assert n.is_visible_to("TREASURY") is False


def test_bank_wide_visible_to_all(sample_notice):
    assert sample_notice.department is None
    assert sample_notice.is_visible_to("ANY_DEPT") is True
    assert sample_notice.is_visible_to(None) is True


def test_enum_behaviour():
    assert Category.COMPLIANCE.acknowledgement_required is True
    assert Category.HR.acknowledgement_required is False
    assert Category.COMPLIANCE.display_name == "Compliance & Regulatory"
    assert Priority.URGENT.escalated is True
    assert Priority.NORMAL.escalated is False
    # Pinning the CURRENT flat-permissions rule. If publishing is ever restricted,
    # this failing is the point - it forces you to update the intent here.
    assert Role.EMPLOYEE.can_publish is True
    assert Role.ADMIN.can_publish is True
    