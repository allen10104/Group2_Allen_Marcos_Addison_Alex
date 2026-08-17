"""FastAPI application entry point."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, notices
from app.config import settings
from app.dependencies import (
    get_auth_service,
    get_employee_repository,
    get_notice_repository,
    get_notice_service,
)
from app.domain.enums import Category, Priority, Role
from app.errors import AccessDeniedError, InvalidCredentialsError, NoticeNotFoundError
from app.schemas.common import ApiError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Notice Board API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notices.router)
app.include_router(auth.router)


@app.exception_handler(StarletteHTTPException)
def handle_http_exception(request: Request, exc: StarletteHTTPException):
    """Makes 401s and 403s come back in the SAME ApiError shape as every other error.

    Without this, FastAPI returns {"detail": "..."} and the React client needs two
    different error parsers."""
    names = {401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed"}
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiError(
            status=exc.status_code,
            error=names.get(exc.status_code, "Error"),
            message=str(exc.detail),
            path=request.url.path,
        ).model_dump(mode="json"),
        # Preserve WWW-Authenticate - dropping headers in a custom handler is an easy
        # thing to get wrong.
        headers=getattr(exc, "headers", None),
    )


# ---------------------------------------------------------------------------
# Exception handlers — one place that turns exceptions into HTTP responses
# ---------------------------------------------------------------------------
# The alternative — try/except in each route — means 5 routes x 4 error types = 20
# blocks that drift out of sync. This is one file, and it guarantees every error the
# frontend sees has the same JSON shape.

def _error(status_code: int, error: str, message: str, request: Request, field_errors=None):
    return JSONResponse(
        status_code=status_code,
        content=ApiError(
            status=status_code, error=error, message=message,
            path=request.url.path, field_errors=field_errors,
        ).model_dump(mode="json"),
    )


@app.exception_handler(NoticeNotFoundError)
def handle_not_found(request: Request, exc: NoticeNotFoundError):
    return _error(404, "Not Found", str(exc), request)


@app.exception_handler(AccessDeniedError)
def handle_forbidden(request: Request, exc: AccessDeniedError):
    """403 — authenticated but not permitted. Distinct from 401 (see Phase 5)."""
    return _error(403, "Forbidden", str(exc), request)


@app.exception_handler(InvalidCredentialsError)
def handle_bad_credentials(request: Request, exc: InvalidCredentialsError):
    return _error(401, "Unauthorized", "Invalid username or password", request)


@app.exception_handler(ValueError)
def handle_value_error(request: Request, exc: ValueError):
    """Domain validation from Notice.create() -> 400, not a 500."""
    return _error(400, "Bad Request", str(exc), request)


@app.exception_handler(RequestValidationError)
def handle_validation(request: Request, exc: RequestValidationError):
    """Pydantic rejected the body -> 400 with per-field messages.

    FastAPI's default is a 422 with a nested `detail` array. We flatten it to
    field -> message and use 400, so the React form can highlight the exact input
    and the error shape matches every other error the API returns."""
    field_errors = {}
    for err in exc.errors():
        # loc looks like ("body", "title"); the last element is the field name.
        field = str(err["loc"][-1])
        field_errors[field] = err.get("msg", "invalid")
    return _error(400, "Bad Request", "Validation failed", request, field_errors)


# ---------------------------------------------------------------------------
# Health + seed
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "UP",
        "service": "notice-board",
        "repository": settings.repository,
        "time": datetime.now(timezone.utc).isoformat(),
    }


def seed_employees():
    """Demo accounts. In production these come from the bank's identity provider and
    this function does not exist.

    Every password goes through hash_password() - there is no path in this codebase
    that writes a plaintext password to storage."""
    repo = get_employee_repository()
    if repo.count() > 0:
        log.info("Employees already present - skipping employee seed")
        return

    service = get_auth_service()
    service.register("E10001", "p.raman", "Compliance123!", "Priya Raman",
                     "COMPLIANCE", {Role.MANAGER})
    service.register("E10002", "m.webb", "ItOps123!", "Marcus Webb",
                     "IT_OPERATIONS", {Role.MANAGER})
    service.register("E10009", "a.admin", "Admin123!", "Alex Admin",
                     "TECHNOLOGY", {Role.ADMIN})
    service.register("E20055", "j.teller", "Teller123!", "Jordan Teller",
                     "RETAIL_BANKING", {Role.EMPLOYEE})

    log.info("Seeded %d employees", repo.count())


@app.on_event("startup")
def seed_data():
    """Three realistic notices so the board is never empty.

    An empty board can't tell you whether your GET works or your POST silently
    failed. The count check makes this idempotent, so it keeps working unchanged
    against Mongo in Phase 3 instead of re-inserting duplicates on every restart.
    """
    seed_employees()

    repo = get_notice_repository()
    if repo.find_all():
        log.info("Notices already present — skipping seed")
        return

    service = get_notice_service()
    now = datetime.now(timezone.utc)

    service.publish(
        title="Q3 AML refresher training — mandatory by Sept 30",
        body="All client-facing staff must complete the Anti-Money-Laundering refresher "
             "in LearnCiti before September 30. Branch managers are accountable for "
             "100% completion in their teams.",
        author_employee_id="E10001", author_name="Priya Raman (Compliance)",
        category=Category.COMPLIANCE, priority=Priority.URGENT,
        expires_at=now + timedelta(days=30),
    )
    service.publish(
        title="Core banking maintenance — Saturday 02:00-05:00 ET",
        body="The core banking platform will be unavailable during this window. Teller "
             "terminals fall back to offline mode. Do not process wire transfers until "
             "the all-clear notice is posted.",
        author_employee_id="E10002", author_name="Marcus Webb (IT Operations)",
        category=Category.IT_SYSTEMS, priority=Priority.HIGH,
        expires_at=now + timedelta(days=7),
    )
    service.publish(
        title="New branch dress code effective October 1",
        body="Business casual is now permitted Monday through Thursday. "
             "Client-meeting days remain business formal.",
        author_employee_id="E10003", author_name="Dana Cole (HR)",
        category=Category.HR, priority=Priority.LOW, department="RETAIL_BANKING",
    )

    log.info("Seeded %d notices", len(repo.find_all()))
    