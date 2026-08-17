"""HTTP layer for notices.

Its entire job: parse the request, call the service, shape the response. There is no
business logic here, and there shouldn't be — the moment a rule lands in a route it
becomes untestable without spinning up the whole app.
"""

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_notice_service
from app.domain.enums import Category
from app.schemas.auth import CurrentUser
from app.schemas.notice import NoticeCreate, NoticeResponse
from app.security.deps import get_current_user
from app.services.notice_service import NoticeService

router = APIRouter(prefix="/api/notices", tags=["notices"])

# The Phase 2 placeholder constants are gone. READS ARE PUBLIC — anyone can open the
# site and see the live board, which is what the assignment's Tier 1 acceptance
# criterion requires. WRITES declare `me: CurrentUser = Depends(get_current_user)`,
# so posting requires a login and the author / acting employee come from the verified
# JWT rather than from anything the client can put in the request body.


@router.get("", response_model=list[NoticeResponse])
def get_board(
    category: Category | None = None,
    department: str | None = None,
    service: NoticeService = Depends(get_notice_service),
):
    """Public: the React app renders the live feed before anyone signs in."""
    return [NoticeResponse.from_domain(n) for n in service.get_board(category, department)]


@router.get("/{notice_id}", response_model=NoticeResponse)
def get_one(
    notice_id: str,
    service: NoticeService = Depends(get_notice_service),
):
    """Public, for the same reason as the board. 404 comes from the exception handler."""
    return NoticeResponse.from_domain(service.get_by_id(notice_id))


@router.post("", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
def create(
    payload: NoticeCreate,
    response: Response,
    me: CurrentUser = Depends(get_current_user),
    service: NoticeService = Depends(get_notice_service),
):
    notice = service.publish(
        title=payload.title,
        body=payload.body,
        # The real author, straight from the signed token. A client CANNOT forge this:
        # it is not a field on NoticeCreate, so Pydantic discards it even if sent.
        author_employee_id=me.employee_id,
        author_name=me.full_name,
        category=payload.category,
        priority=payload.priority,
        department=payload.department,
        expires_at=payload.expires_at,
    )
    response.headers["Location"] = f"/api/notices/{notice.id}"
    return NoticeResponse.from_domain(notice)


@router.put("/{notice_id}", response_model=NoticeResponse)
def update(
    notice_id: str,
    payload: NoticeCreate,
    me: CurrentUser = Depends(get_current_user),
    service: NoticeService = Depends(get_notice_service),
):
    notice = service.update(
        notice_id=notice_id,
        acting_employee_id=me.employee_id,      # the checkpoint now gets real data
        title=payload.title, body=payload.body,
        category=payload.category, priority=payload.priority,
        department=payload.department, expires_at=payload.expires_at,
    )
    return NoticeResponse.from_domain(notice)


@router.delete("/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    notice_id: str,
    me: CurrentUser = Depends(get_current_user),
    service: NoticeService = Depends(get_notice_service),
):
    service.archive(notice_id, me.employee_id)
