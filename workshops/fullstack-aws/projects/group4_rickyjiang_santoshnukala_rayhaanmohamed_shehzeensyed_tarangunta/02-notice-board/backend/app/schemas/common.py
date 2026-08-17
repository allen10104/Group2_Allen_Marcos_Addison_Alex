"""One error shape for every failure the API can produce."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    """A consistent error body is worth real money on the frontend: React writes one
    error handler instead of guessing whether a 404 came back as a string, an object,
    or FastAPI's default {"detail": ...}."""

    # default_factory, NOT `datetime.now(timezone.utc)` as a plain default: a bare
    # default is evaluated ONCE at import, so every error in the process would carry
    # the server's start-up time. The factory runs per instance.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    status: int          # the HTTP status, repeated in the body so a logged payload is
                         # self-contained without its response headers
    error: str           # short reason phrase: "Not Found", "Unauthorized"
    message: str         # human-readable detail, safe to show a user
    path: str            # which endpoint failed - the first thing you want when a
                         # screenshot of an error arrives with no other context

    # Populated only for validation failures: {"title": "must not be blank"}. React
    # reads it in NoticeForm to highlight the exact input rather than showing one
    # generic message at the top of the form.
    field_errors: dict[str, str] | None = None
    