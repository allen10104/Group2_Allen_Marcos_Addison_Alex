# Import UUID for typing the notice_id path parameter.
from uuid import UUID
# Import FastAPI's router, dependency injection helper, and exception class.
from fastapi import APIRouter, Depends, HTTPException
# Import notice_service, which holds the database logic for notices.
from services import notice_service
# Import get_current_user, the dependency that resolves the caller from their JWT.
from security.dependencies import get_current_user
# Import the Pydantic request/response models used for validation.
from models import schemas
# Import datetime and timedelta to compute an optional expiry timestamp.
from datetime import datetime, timedelta

# Create a router for notice endpoints, prefixing all its routes with "/notices".
router = APIRouter(prefix="/notices")

# Register this function as the handler for GET /notices/, returning a list of notice_Out.
@router.get("/", response_model=list[schemas.notice_Out])
# Define the async handler; no auth required to view notices.
async def get_all_notices():
    # Fetch and return every notice from the database.
    return await notice_service.get_all_notices()

# Register this function as the handler for POST /notices/, returning a single notice_Out.
@router.post("/", response_model=schemas.notice_Out)
# Define the async handler, requiring a validated body and an authenticated current_user.
async def create_notice(notice: schemas.notice_Create, current_user: dict = Depends(get_current_user)):
    # Convert expires_in_days into an absolute expiry timestamp, or leave it unset.
    expires_at = datetime.utcnow() + timedelta(days=notice.expires_in_days) if notice.expires_in_days else None
    # Create the notice under the authenticated user's id, carrying its pin state and expiry.
    return await notice_service.create_notice(current_user["id"], current_user["email"], notice.message, notice.is_pinned, expires_at)

# Register this function as the handler for GET /notices/{notice_id}, returning a single notice_Out.
@router.get("/{notice_id}", response_model=schemas.notice_Out)
# Define the async handler, taking the notice's id from the URL path.
async def get_notice_by_id(notice_id: UUID):
    # Look up the notice by its id.
    notice = await notice_service.get_notice_by_id(notice_id)
    # If no notice matched that id, return a 404.
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    # Return the found notice.
    return notice

# Register this function as the handler for DELETE /notices/{notice_id}.
@router.delete("/{notice_id}")
# Define the async handler, requiring authentication so only the owner can delete.
async def delete_notice(notice_id: UUID, current_user: dict = Depends(get_current_user)):
    # Attempt to delete the notice, scoped to the authenticated user's id.
    deleted = await notice_service.delete_notice(notice_id, current_user["id"])
    # If nothing was deleted (wrong id or not the owner), return a 404.
    if deleted is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    # Return the deleted notice's data.
    return deleted

# Register this function as the handler for PATCH /notices/{notice_id}/pin, returning a single notice_Out.
@router.patch("/{notice_id}/pin", response_model=schemas.notice_Out)
# Define the async handler, requiring authentication so only the owner can (un)pin.
async def pin_notice(notice_id: UUID, payload: schemas.notice_Pin, current_user: dict = Depends(get_current_user)):
    # Update the notice's pinned status, scoped to the authenticated user's id.
    updated = await notice_service.set_notice_pin(notice_id, current_user["id"], current_user["email"], payload.is_pinned)
    # If nothing was updated (wrong id or not the owner), return a 404.
    if updated is None:
        raise HTTPException(status_code=404, detail="Notice not found")
    # Return the updated notice's data.
    return updated
