from backend.models.category import Category
from backend.models.notice import Notice
from backend.models.user import User
from backend.auth.passwords import hash_password


def _notice_owned_by(author_id: int) -> Notice:
    notice = Notice(1, "T", "2026-08-16", "C", Category.GENERAL)
    notice.author_id = author_id
    notice.author = "Owner"
    return notice


def test_user_construct():
    user = User(1, "Alice", "a@x.com", hash_password("secret"), is_admin=False)
    assert user.id == 1
    assert user.email == "a@x.com"
    assert user.is_admin is False
    assert "secret" not in user.password_hash


def test_can_modify_own_notice():
    user = User(10, "Alice", "a@x.com", hash_password("x"))
    assert user.can_modify(_notice_owned_by(10)) is True


def test_cannot_modify_others_notice():
    user = User(10, "Alice", "a@x.com", hash_password("x"))
    assert user.can_modify(_notice_owned_by(20)) is False


def test_admin_can_modify_any_notice():
    admin = User(99, "Admin", "admin@x.com", hash_password("x"), is_admin=True)
    assert admin.can_modify(_notice_owned_by(20)) is True
