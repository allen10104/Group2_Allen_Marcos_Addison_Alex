"""Creates and verifies JSON Web Tokens."""

from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.domain.employee import Employee

# A JWT is three base64url segments joined by dots:
#
#   header.payload.signature
#
# The header and payload are ENCODED, NOT ENCRYPTED - paste any token into jwt.io and
# you can read every claim. The signature is what makes it trustworthy: it proves the
# payload has not been altered since we signed it. Two consequences:
#
#   1. NEVER put a secret in a claim. The user can read all of it.
#   2. ALWAYS verify the signature before trusting any claim. An attacker can craft a
#      token claiming roles:["ADMIN"] in about four seconds.


def create_access_token(employee: Employee) -> tuple[str, int]:
    """Mint a token for a successfully-authenticated employee.

    Returns (token, expires_in_seconds).

    The claims answer every authorization question WITHOUT another database read. On
    Lambda that matters - a DB round trip per request would add latency to every call.
    That is the core JWT trade-off: you buy statelessness by accepting that a token
    stays valid until it expires, even if you disable the account meanwhile. One hour
    of exposure is the price; short expiry is the mitigation.
    """
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)

    payload = {
        # "sub" - the standard subject claim.
        "sub": employee.username,
        "employee_id": employee.employee_id,
        "full_name": employee.full_name,
        "department": employee.department,
        # Plain strings: enums do not survive a JSON round trip cleanly.
        "roles": sorted(r.value for r in employee.roles),
        "iat": now,
        "exp": now + expires_delta,
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict:
    """Verify signature + expiry and return the claims.

    Raises jwt.PyJWTError on anything wrong. The caller catches it and returns a clean
    401 rather than a 500.

    `algorithms=[...]` is NOT optional and NOT cosmetic. Without it PyJWT would trust
    the algorithm declared in the token's own header - and an attacker who sets
    "alg": "none" gets an unsigned token accepted. Pinning it server-side is the fix
    for one of the best-known JWT vulnerabilities.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
