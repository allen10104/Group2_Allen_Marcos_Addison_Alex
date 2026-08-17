"""Domain exceptions.

Plain exception classes carrying no HTTP concepts — no status codes, no FastAPI
imports. Phase 2 maps them to HTTP responses in exactly one place, which keeps the
domain reusable from a CLI, a test, or a message consumer.
"""


class NoticeNotFoundError(Exception):
    """Raised when an id doesn't resolve. Becomes HTTP 404."""

    def __init__(self, notice_id: str):
        self.notice_id = notice_id
        super().__init__(f"Notice not found: {notice_id}")


class AccessDeniedError(Exception):
    """Authenticated but not permitted to act on this resource. Becomes HTTP 403."""


class InvalidCredentialsError(Exception):
    """Bad username or password. Becomes HTTP 401.

    ONE exception type for both "no such user" and "wrong password", deliberately.
    Distinct errors let an attacker enumerate valid usernames — "user not found" vs
    "wrong password" tells them which half to keep guessing. At a bank that's a
    findable defect in a pen test."""
    