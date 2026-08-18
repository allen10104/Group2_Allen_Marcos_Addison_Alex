# APIRouter lets us define these routes in their own file and plug them into
# main.py's app. Depends is how FastAPI hands the Supabase client to an
# endpoint. HTTPException is how we return a chosen status code instead of
# letting an error surface as a 500.
from fastapi import APIRouter, Depends, HTTPException

# Client is only used as a type annotation on the injected argument.
from supabase import Client

# get_client builds the Supabase client once and returns the same one after.
from app.db import get_client

# The request and response shapes, kept in one place so the controller stays
# about routing.
from app.models.user import TokenResponse, UserCreate, UserLogin, UserOut

# The service that does the actual work. Imported as a module rather than as
# loose function names, so a call reads as auth_service.login and says
# plainly that the work happens a layer down.
from app.services import auth_service

# Create the router for authentication endpoints.
#
# prefix means every path below is relative to /auth, which keeps signing up
# and logging in visibly separate from the notice routes on the /docs page.
router = APIRouter(prefix="/auth", tags=["auth"])


# POST /auth/signup
# Creates an account from a JSON body of
# {"username": "...", "password": "..."}.
#
# 201 because a new resource was created. response_model=UserOut is doing
# real work here, not just documentation: the service returns the whole
# database row, and this is what strips it down to id and username so the
# hash can never reach the client.
#
# No token is issued. Signing up and logging in stay separate so there is one
# path that mints a token, which is easier to reason about than two. The
# client posts to /auth/login straight afterwards.
@router.post("/signup", response_model=UserOut, status_code=201)
def signup(credentials: UserCreate, client: Client = Depends(get_client)):
    # The service refuses a blank username or an over-long password with a
    # ValueError. 422 matches what FastAPI already returns for a body that
    # fails validation, so the caller sees one consistent answer for "your
    # body was not acceptable".
    try:
        user = auth_service.signup(
            client,
            username=credentials.username,
            password=credentials.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # None means the username is taken. 409 Conflict is the honest answer:
    # the request was well formed and the caller may retry with a different
    # username, which is not what 400 or 422 would suggest.
    #
    # This does tell an anonymous caller which usernames exist. That is
    # unavoidable for a signup form that has to explain why it refused, and
    # it is the reason the login route below stays vague instead.
    if user is None:
        raise HTTPException(
            status_code=409,
            detail="That username is already taken",
        )

    return user


# POST /auth/login
# Exchanges a username and password for a signed token.
#
# The body is UserLogin, not UserCreate. See the comment on UserLogin: the
# signup rules must not run here, or a mistyped short password is answered
# with a 422 quoting the password policy instead of a 401.
#
# 200 rather than 201: logging in creates no resource, it just hands back a
# token for an account that already exists.
@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, client: Client = Depends(get_client)):
    token = auth_service.login(
        client,
        username=credentials.username,
        password=credentials.password,
    )

    # None covers both an unknown username and a wrong password, and the
    # message deliberately does not say which. Telling a caller that a
    # username exists lets them work through a list of usernames before they
    # start guessing passwords.
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # token_type defaults to "bearer" on the model, so it does not have to be
    # repeated here.
    return TokenResponse(access_token=token)
