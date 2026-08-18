# Depends is how FastAPI wires one function into another. HTTPException is
# how we answer with a 401 when a token does not hold up.
from fastapi import Depends, HTTPException

# HTTPBearer reads the "Authorization: Bearer <token>" header for us and is
# what puts the Authorize button on the /docs page.
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from supabase import Client

from app.db import get_client
from app.services import auth_service

# auto_error=False stops HTTPBearer from raising its own 403 when the header
# is missing, so we can answer with a 401 instead. A missing token means "you
# have not identified yourself", which is what 401 says. 403 would mean "we
# know who you are and you still may not do this", and that is the wrong
# message here.
bearer_scheme = HTTPBearer(auto_error=False)


# The caller behind the current request.
#
# A small class rather than a raw dict so that a route reads
# current_user.user_id instead of current_user["id"], and so a typo is an
# AttributeError at the point of use rather than a silent None.
class CurrentUser:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username


# FastAPI dependency that turns an incoming Authorization header into a
# CurrentUser, and rejects the request if it cannot.
#
# Any route that adds current_user: CurrentUser = Depends(get_current_user)
# becomes protected, because the request never reaches the route body unless
# this function returns successfully.
#
# This does query the database, unlike the equivalent in BankingApp. The
# claims are signed by us and could be trusted without a second lookup, so
# the round trip buys exactly one thing: a token belonging to a deleted
# account stops working immediately instead of staying valid until it
# expires. Given tokens last 24 hours here, and given the backend now holds
# the service_role key and is the only thing standing between a caller and
# the data, that is worth one indexed primary key read per request.
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    client: Client = Depends(get_client),
):
    return _authenticate(credentials, client)


# The rules for turning credentials into a user, with no FastAPI wiring of
# its own.
#
# Split out so that the strict and the optional dependency below share one
# implementation. Two copies would drift, and the copy that drifted would be
# the one deciding who is allowed in.
#
# Still raises HTTPException rather than returning None on failure, because
# the specific reason is worth reporting when a route demands a token. The
# optional wrapper throws that detail away deliberately.
def _authenticate(credentials, client):
    # No Authorization header at all, or one that was not a Bearer header.
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            # The spec says a 401 must say how to authenticate. Some clients
            # rely on this header to know they should retry with a token.
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = auth_service.decode_access_token(credentials.credentials)
    except auth_service.TokenError as error:
        # Expired and malformed tokens both land here.
        raise HTTPException(
            status_code=401,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = payload.get("sub")

    # A token we signed always carries sub. If it is missing, the token is
    # structurally wrong even though the signature checked out.
    if subject is None:
        raise HTTPException(
            status_code=401,
            detail="Token is missing the subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # sub is stored as a string to satisfy the JWT spec, so it has to come
    # back to an int before it can be compared against notices.user_id. A
    # token carrying a non-numeric sub was not issued by us in any form we
    # recognise, so it is refused rather than allowed to raise later.
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Token subject is not a valid user id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(client, user_id)

    # The signature was good but the account is gone, so the token refers to
    # nobody. 401 rather than 404: the request failed to identify a valid
    # caller, which is an authentication problem, and the route it was aimed
    # at is not the thing that is missing.
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(user_id=user["id"], username=user["username"])


# Like get_current_user, but hands back None instead of refusing the request
# when there is no usable token.
#
# This is what lets GET /notices serve everybody. A signed in caller is
# identified, so their own reactions come back highlighted, and a signed out
# one still gets the notices and the counts. Without it the route would have
# to choose between being public and knowing who is asking.
#
# A token that is present but bad, expired, forged, or pointing at a deleted
# account, is treated exactly like no token at all. That is deliberate on a
# route that does not require authentication: the reasonable answer is the
# public view, not an error, since nothing on the page depended on the token
# in the first place. A route that genuinely needs identity uses
# get_current_user, where every one of those cases is a 401 with a reason.
#
# The consequence worth knowing: a frontend whose token quietly expires sees
# the board keep working with its reactions no longer highlighted, rather
# than being told. Posting or reacting is what surfaces the 401.
def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    client: Client = Depends(get_client),
):
    if credentials is None:
        return None

    try:
        return _authenticate(credentials, client)
    except HTTPException:
        return None
