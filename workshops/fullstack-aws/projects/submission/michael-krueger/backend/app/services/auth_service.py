# datetime is how we stamp a token with its expiry. timezone.utc keeps the
# clock unambiguous, since the server and the database may sit in different
# time zones.
from datetime import datetime, timedelta, timezone

# lru_cache remembers the signing key after the first read, the same way
# app/db.py caches the Supabase client.
from functools import lru_cache

# os.getenv reads the signing key out of the environment, so it is never
# written in the source.
import os

# bcrypt hashes a password on the way in and checks one on the way back. The
# salt is embedded in the hash itself, so checkpw pulls it back out and does
# not need it passed separately.
import bcrypt

# PyJWT does the actual signing and verification.
import jwt

# load_dotenv copies the values out of the .env file into the environment.
from dotenv import load_dotenv

from supabase import Client

# The table holding credentials. The notices table is handled in
# notice_service.py, and neither service reaches into the other's table.
TABLE = "users"

# The columns read back after a signup. password_hash is deliberately not in
# this list: nothing outside this module has any reason to see it, and the
# surest way to keep a hash out of a response is never to select it.
COLUMNS = "id, username, created_at"

# HS256 signs with a single shared secret, which is the right choice when the
# same application both issues and verifies the tokens. The alternatives use
# a public/private key pair, which only helps when a separate service needs
# to verify tokens without being able to create them.
JWT_ALGORITHM = "HS256"

# How long an access token stays valid. A day is a reasonable middle ground
# for a training project: long enough that nobody is logging in every hour,
# short enough that a leaked token stops working on its own.
#
# There is no logout that invalidates a token on the server. A JWT is valid
# until it expires, because nothing tracks issued tokens, so this number is
# the real upper bound on how long a stolen token is useful.
ACCESS_TOKEN_EXPIRE_HOURS = 24

# bcrypt refuses anything longer than 72 bytes. Older versions truncated
# silently, which was worse, because two different long passwords could
# unlock the same account.
BCRYPT_MAX_BYTES = 72


# Raised when a token cannot be trusted, whether it was tampered with, signed
# with the wrong key, or simply expired.
#
# The dependency catches this and turns it into a 401. Defining our own error
# means the rest of the application never has to import PyJWT just to name
# the exceptions it might see.
class TokenError(Exception):
    pass


# Reads the signing key, once.
#
# Lazy and cached for the same reason as get_client in app/db.py: nothing
# should raise while this module is being imported. If it did, the whole app
# would fail to start and even /health would be unreachable, which is exactly
# the endpoint you want answering while you work out that the config is
# wrong. Reading it at first use means the app starts and only the routes
# that actually sign or verify a token fail, with a message saying what to
# fix.
#
# Anyone holding this key can mint a token for any user, which is why it
# lives in .env and not here.
@lru_cache(maxsize=1)
def _get_jwt_secret():
    load_dotenv()

    secret = os.getenv("JWT_SECRET")

    if not secret:
        raise RuntimeError(
            "JWT_SECRET is not set. Copy .env.example to .env and fill it in. "
            'Generate one with: python -c "import secrets; '
            'print(secrets.token_hex(32))"'
        )

    return secret


# Hashes a plain password for storage.
#
# gensalt makes a fresh random salt every call, so two users who pick the
# same password still end up with different hashes, and a stolen database
# cannot be cracked by hashing a dictionary once and comparing.
#
# Raises ValueError if the password is too long for bcrypt. The model already
# caps the length in characters, but bcrypt counts bytes and a password of
# accented characters or emoji is longer in bytes than it looks, so the real
# check has to happen here.
def hash_password(password: str):
    encoded = password.encode()

    if len(encoded) > BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Password must be {BCRYPT_MAX_BYTES} bytes or fewer once encoded."
        )

    # hashpw returns bytes. The column is text, so it is decoded here rather
    # than letting the client store the repr of a bytes object.
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode()


# Checks a typed password against a stored hash.
#
# Returns False rather than raising on a malformed hash or an over-long
# password. Both mean "this login does not succeed", and turning them into
# exceptions would make an ordinary failed login look like a server fault.
def verify_password(password: str, password_hash: str):
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


# Builds a signed access token for a user who has already proven who they
# are.
#
# This function checks no password. By the time it runs, login below has
# already verified the credentials, and this only records the result in a
# form the client can hand back on later requests.
#
# user_id goes in the "sub" claim, which is the standard place for "who this
# token is about". It goes in as a string because the JWT spec expects one,
# and some libraries reject a numeric sub outright.
def create_access_token(user_id, username, expires_delta=None):
    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    # The payload is the set of claims travelling inside the token.
    #
    # Everything here is readable by anyone holding the token. A JWT is
    # signed, not encrypted, so it proves nobody altered the contents, but it
    # does not hide them. Never put a password or a hash in this dictionary.
    payload = {
        "sub": str(user_id),
        "username": username,
        # Expiry, as a UNIX timestamp. PyJWT checks this automatically when
        # the token is decoded.
        "exp": now + expires_delta,
        # When the token was issued. Useful for auditing, and it would let us
        # invalidate everything issued before a given moment if we ever need
        # to.
        "iat": now,
    }

    return jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)


# Verifies a token and hands back the claims inside it.
#
# Decoding is the security boundary of the whole application. If the
# signature does not match our key, the token was not issued by us and
# nothing in it can be believed. PyJWT raises in that case, and it also
# raises once the exp claim has passed, so both checks happen here.
def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            # Passing the algorithm explicitly matters. Letting the token
            # name its own algorithm is a well known way to forge one,
            # because an attacker can ask for "none" and skip the signature
            # entirely.
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError:
        # Covers a bad signature, a malformed string, and anything else PyJWT
        # refuses to accept.
        raise TokenError("Token is invalid")

    return payload


# Finds one user by username, including the password hash.
#
# Private to this module, hence the leading underscore. It is the one query
# that selects password_hash, and keeping it here means no controller can
# reach a hash by accident.
def _get_user_by_username(client: Client, username: str):
    response = (
        client.table(TABLE)
        .select("id, username, password_hash")
        .eq("username", username)
        .maybe_single()
        .execute()
    )

    # maybe_single can return None for the whole response rather than just
    # for .data, depending on how the request was answered. Checking the
    # response first avoids an AttributeError on the miss path.
    if response is None:
        return None

    return response.data


# Finds one user by id, without the password hash.
#
# Used by the get_current_user dependency to confirm the account behind a
# token still exists.
def get_user_by_id(client: Client, user_id: int):
    response = (
        client.table(TABLE)
        .select(COLUMNS)
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )

    if response is None:
        return None

    return response.data


# Registers a new user and returns the created row.
#
# Returns None when the username is already taken, following the same pattern
# as the notice service: the service reports what happened and the controller
# decides which status code that maps to.
#
# The check and the insert are two separate statements, so two people
# claiming the same username in the same instant could both pass the check.
# The unique constraint on users.username is what actually prevents the
# duplicate, and the loser of that race gets a 500 rather than a tidy 409.
# Worth knowing, not worth solving here: fixing it properly means catching
# the constraint violation by its Postgres error code, which ties this
# module to the exact error shape PostgREST returns.
def signup(client: Client, username: str, password: str):
    username = username.strip()

    if not username:
        raise ValueError("username cannot be blank")

    if _get_user_by_username(client, username) is not None:
        return None

    # Raises ValueError for an over-long password, which the controller turns
    # into a 422.
    password_hash = hash_password(password)

    response = (
        client.table(TABLE)
        .insert({"username": username, "password_hash": password_hash})
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


# Checks a username and password and hands back a signed access token.
#
# Returns None when the login fails, whichever half was wrong.
#
# Deliberately does not say which of the two was wrong, and deliberately runs
# the same amount of work either way is not quite true here: an unknown
# username returns before any hashing happens, which is measurably faster
# than a wrong password. That timing difference can reveal which usernames
# exist. It is left as is because the fix costs a bcrypt verification on
# every failed login, and the same information is already available from
# signup, which has to reject a duplicate username to be useful at all.
def login(client: Client, username: str, password: str):
    user = _get_user_by_username(client, username.strip())

    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return create_access_token(user_id=user["id"], username=user["username"])
