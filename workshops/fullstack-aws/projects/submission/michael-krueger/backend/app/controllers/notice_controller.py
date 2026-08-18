# APIRouter lets us define these routes in their own file and plug them into
# main.py's app. Depends is how FastAPI hands the Supabase client and the
# signed-in user to an endpoint. HTTPException is how we return a chosen
# status code instead of letting an error surface as a 500.
from fastapi import APIRouter, Depends, HTTPException

# Client is only used as a type annotation on the injected argument.
from supabase import Client

# get_client builds the Supabase client once and returns the same one after.
from app.db import get_client

# get_current_user verifies the JWT and identifies who is calling.
# CurrentUser is what it hands back once the check passes.
from app.dependencies import (
    CurrentUser,
    get_current_user,
    get_current_user_optional,
)

# The request and response shapes, kept in one place so the controller stays
# about routing.
from app.models.notice import NoticeCreate, NoticeOut

# The service that does the actual work. Imported as a module rather than as
# loose function names, so a call reads as notice_service.create_notice and
# says plainly that the work happens a layer down.
from app.services import notice_service

# Create the router for notice related endpoints.
#
# prefix means every path below is relative to /notices, so the paths read
# as "" and "/{notice_id}" instead of repeating the word three times.
# tags is what groups these endpoints together on the /docs page.
router = APIRouter(prefix="/notices", tags=["notices"])


# Every endpoint here is deliberately thin. It takes the request apart,
# calls one service function, and turns what comes back into a status code.
# No endpoint builds a query, and none of them mention the notices table.
#
# The ownership rule is not enforced here either. This layer only knows that
# a NoticeOwnershipError means 403. Deciding who owns what is the service's
# job, which keeps the rule in one place rather than spread across the
# routes that happen to need it.


# GET /notices
# Returns every notice, newest first, each with its reaction summary.
#
# Still public, and now optionally authenticated, which are not the same
# thing. get_current_user_optional never refuses a request: it identifies the
# caller when it can and yields None when it cannot. It is a notice board,
# so the wall can be read without an account, but knowing who is reading
# means their own reactions can come back marked as theirs.
#
# So an anonymous viewer sees every notice and every count, with
# my_reactions empty. A signed in viewer sees the same counts plus which of
# them are their own.
#
# response_model on the decorator, rather than a return annotation alone, is
# what makes FastAPI filter each row down to the fields in NoticeOut.
@router.get("", response_model=list[NoticeOut])
def list_notices(
    client: Client = Depends(get_client),
    current_user: CurrentUser | None = Depends(get_current_user_optional),
):
    # The service takes an id or None rather than a CurrentUser, so it stays
    # unaware of how callers are authenticated.
    return notice_service.list_notices(
        client,
        current_user_id=current_user.user_id if current_user else None,
    )


# POST /notices
# Creates one notice from a JSON body of {"name": "...", "message": "..."}.
#
# Requires a valid token. Adding get_current_user to the signature is what
# makes that true: FastAPI runs the dependency first and answers 401 without
# ever entering this function if the token is missing, expired or forged.
#
# 201 rather than the default 200, because a new resource was created. The
# created notice is returned in full so the frontend can add it to the list
# without re-fetching everything, and so the caller learns the id.
@router.post("", response_model=NoticeOut, status_code=201)
def create_notice(
    notice: NoticeCreate,
    client: Client = Depends(get_client),
    current_user: CurrentUser = Depends(get_current_user),
):
    # The service refuses a name or message that is blank once trimmed and
    # says so with a ValueError. Turning it into a 422 here matches the code
    # FastAPI already uses for a body that fails validation, so a caller
    # sees one consistent answer for "your body was not acceptable".
    #
    # The author is current_user.user_id, taken from the verified token. The
    # request body has no say in it, which is what stops anyone posting a
    # notice under another account's name.
    try:
        created = notice_service.create_notice(
            client,
            notice,
            user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # None means the insert wrote nothing, which is worth saying clearly
    # instead of letting it become an unexplained 500 further down.
    if created is None:
        raise HTTPException(
            status_code=500,
            detail="Notice was not created.",
        )

    return created


# DELETE /notices/{notice_id}
# Deletes one notice, if the caller posted it.
#
# 204 means "done, and there is nothing to send back", which is the usual
# answer for a delete. There is no body, so no response_model here.
#
# notice_id is annotated int, so /notices/abc is answered with a 422 by
# FastAPI before this function ever runs.
@router.delete("/{notice_id}", status_code=204)
def delete_notice(
    notice_id: int,
    client: Client = Depends(get_client),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        deleted = notice_service.delete_notice(
            client,
            notice_id,
            requesting_user_id=current_user.user_id,
        )
    except notice_service.NoticeOwnershipError as exc:
        # 403, not 401. The caller proved who they are, and the answer is
        # still no. A 401 would wrongly suggest that logging in again might
        # help.
        raise HTTPException(status_code=403, detail=str(exc))

    # False means nothing had that id. Answering 404 tells the caller the
    # notice was already gone, which is more useful than a silent 204 that
    # looks like success.
    if not deleted:
        raise HTTPException(status_code=404, detail="Notice not found")

    # Nothing is returned. FastAPI sends the empty 204 response on its own.
    return None
