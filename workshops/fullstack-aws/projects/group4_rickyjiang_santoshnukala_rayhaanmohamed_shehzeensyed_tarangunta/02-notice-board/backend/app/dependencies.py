"""Wiring: which concrete implementations the routes receive.

FastAPI's dependency injection is the seam. A route declares
`service: NoticeService = Depends(get_notice_service)` and never constructs
anything itself — so a test can override the dependency with a fake in one line.
"""

from functools import lru_cache

from app.config import settings
from app.repositories.base import EmployeeRepository, NoticeRepository


@lru_cache(maxsize=1)
def get_notice_repository() -> NoticeRepository:
    """Built once and reused for the life of the process.

    @lru_cache is doing singleton duty here. It matters for two different reasons:
    with the in-memory repo it's essential (a new dict per request would lose every
    notice instantly), and with Mongo in Phase 3 it means ONE connection pool instead
    of a new client per request — which on Lambda is the difference between a warm
    50ms response and a fresh TLS handshake every time.

    Phase 3 adds the mongo branch here. This function is the entire swap.
    """
    if settings.repository == "mongo":
        from app.repositories.mongo import MongoNoticeRepository  # noqa: PLC0415
        return MongoNoticeRepository()

    from app.repositories.memory import InMemoryNoticeRepository
    return InMemoryNoticeRepository()


@lru_cache(maxsize=1)
def get_employee_repository() -> EmployeeRepository:
    if settings.repository == "mongo":
        from app.repositories.mongo import MongoEmployeeRepository  # noqa: PLC0415
        return MongoEmployeeRepository()

    from app.repositories.memory import InMemoryEmployeeRepository
    return InMemoryEmployeeRepository()


def get_notice_service():
    """Request-scoped service over a process-scoped repository.

    The service itself is stateless, so constructing one per request costs nothing
    and keeps it trivially testable."""
    from app.services.notice_service import NoticeService
    return NoticeService(get_notice_repository())

def get_auth_service():
    """Same request-scoped-service / process-scoped-repository split as above.

    The import is inside the function, matching get_notice_repository: it keeps this
    module free of a hard dependency on the service layer, so `import app.dependencies`
    stays cheap and there is no import cycle when a service imports from here."""
    from app.services.auth_service import AuthService
    return AuthService(get_employee_repository())

