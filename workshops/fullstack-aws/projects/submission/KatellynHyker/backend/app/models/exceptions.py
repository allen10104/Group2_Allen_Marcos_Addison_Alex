"""Domain exceptions.

Services raise these instead of thinking about HTTP at all; main.py maps
each one to a status code in one central place (see its exception handlers).
"""


class AppError(Exception):
    """Base class for every domain exception in this app.

    Stores `detail` (the message) and `status_code` (the HTTP status this
    error maps to) so main.py's handlers -- both the specific ones and the
    generic AppError fallback -- can read exc.detail / exc.status_code
    directly instead of each exception type reimplementing this.
    """

    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    """The requested resource doesn't exist."""

    status_code = 404


class DuplicateError(AppError):
    """Attempted to create something that already exists (e.g. email taken)."""

    status_code = 409


class ForbiddenError(AppError):
    """User is authenticated but does not have permission to perform the action."""

    status_code = 403


class ValidationError(AppError):
    """Request is well-formed but violates a business rule."""

    status_code = 422


class UnauthorizedError(AppError):
    """Missing/invalid credentials, or a valid user acting on someone else's resource."""

    status_code = 401