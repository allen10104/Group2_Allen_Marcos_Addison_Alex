from datetime import date

import pytest

from backend.models.category import Category


def test_create_notice_stamps_author(service, alice):
    notice = service.create_notice(
        "Welcome", "Hello", Category.ANNOUNCEMENT, actor=alice
    )
    assert notice.id == 1
    assert notice.author == "Alice"
    assert notice.author_id == alice.id


def test_create_notice_default_date(service, alice):
    notice = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    assert notice.date == date.today().isoformat()


def test_create_notice_invalid_content_raises(service, alice):
    with pytest.raises(ValueError, match="Content is required"):
        service.create_notice("T", "  ", Category.GENERAL, actor=alice)


def test_get_notice_existing(service, alice):
    created = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    found = service.get_notice(created.id)
    assert found.title == "T"


def test_get_notice_missing_raises(service):
    with pytest.raises(ValueError, match="Notice not found"):
        service.get_notice(999)


def test_update_notice_by_owner(service, alice):
    created = service.create_notice("Old", "C", Category.GENERAL, actor=alice)
    updated = service.update_notice(created.id, alice, title="New")
    assert updated.title == "New"
    assert service.get_notice(created.id).title == "New"


def test_update_notice_by_other_user_raises(service, alice, bob):
    created = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    with pytest.raises(ValueError, match="not authorized"):
        service.update_notice(created.id, bob, title="Hacked")


def test_update_notice_by_admin(service, alice, admin):
    created = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    updated = service.update_notice(created.id, admin, title="Admin edit")
    assert updated.title == "Admin edit"


def test_update_notice_unknown_fields_raises(service, alice):
    created = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    with pytest.raises(ValueError, match="Cannot update fields"):
        service.update_notice(created.id, alice, author="Nope")


def test_delete_notice_by_owner(service, alice):
    created = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    service.delete_notice(created.id, alice)
    with pytest.raises(ValueError, match="Notice not found"):
        service.get_notice(created.id)


def test_delete_notice_by_other_raises(service, alice, bob):
    created = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    with pytest.raises(ValueError, match="not authorized"):
        service.delete_notice(created.id, bob)


def test_delete_notice_by_admin(service, alice, admin):
    created = service.create_notice("T", "C", Category.GENERAL, actor=alice)
    service.delete_notice(created.id, admin)
    with pytest.raises(ValueError, match="Notice not found"):
        service.get_notice(created.id)
