import pytest

from backend.models.category import Category
from backend.models.notice import Notice


def test_valid_construct_leaves_author_unset():
    notice = Notice(
        id=1,
        title="Welcome",
        date="2026-08-16",
        content="Hello",
        category=Category.GENERAL,
    )
    assert notice.id == 1
    assert notice.title == "Welcome"
    assert notice.author is None
    assert notice.author_id is None


def test_empty_title_raises():
    with pytest.raises(ValueError, match="Title is required"):
        Notice(1, "  ", "2026-08-16", "Hello", Category.GENERAL)


def test_empty_content_raises():
    with pytest.raises(ValueError, match="Content is required"):
        Notice(1, "Title", "2026-08-16", "   ", Category.GENERAL)


def test_content_too_long_raises():
    with pytest.raises(ValueError, match="at most"):
        Notice(
            1,
            "Title",
            "2026-08-16",
            "x" * (Notice.MAX_CONTENT_LENGTH + 1),
            Category.GENERAL,
        )


def test_non_category_raises():
    with pytest.raises(ValueError, match="Category"):
        Notice(1, "Title", "2026-08-16", "Hello", "General")


def test_title_and_content_are_stripped():
    notice = Notice(1, "  Hi  ", "2026-08-16", "  Body  ", Category.EVENT)
    assert notice.title == "Hi"
    assert notice.content == "Body"


def test_equality_by_id():
    a = Notice(1, "A", "2026-08-16", "one", Category.OTHER)
    b = Notice(1, "B", "2026-08-16", "two", Category.GENERAL)
    c = Notice(2, "A", "2026-08-16", "one", Category.OTHER)
    assert a == b
    assert a != c
    assert a != "not-a-notice"


def test_validate_standalone():
    with pytest.raises(ValueError, match="Title is required"):
        Notice.validate("", "content", Category.GENERAL)
