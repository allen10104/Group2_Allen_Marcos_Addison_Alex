"""Token and password tests: round-trip, tampering, wrong key, expiry."""

import time

import jwt
import pytest

from app.config import settings
from app.domain.employee import Employee
from app.domain.enums import Role
from app.security.jwt_service import create_access_token, decode_access_token
from app.security.password import hash_password, verify_password


@pytest.fixture
def manager() -> Employee:
    return Employee.create(
        employee_id="E10001", username="p.raman", password_hash="irrelevant",
        full_name="Priya Raman", department="COMPLIANCE", roles={Role.MANAGER},
    )


def test_token_round_trips_every_claim(manager):
    token, expires_in = create_access_token(manager)

    assert len(token.split(".")) == 3            # header.payload.signature
    assert expires_in == settings.jwt_expiration_minutes * 60

    claims = decode_access_token(token)
    assert claims["sub"] == "p.raman"
    assert claims["employee_id"] == "E10001"
    assert claims["roles"] == ["MANAGER"]


def test_tampered_token_is_rejected(manager):
    token, _ = create_access_token(manager)
    # Corrupt one character of the payload. The signature no longer matches the
    # content - precisely what signing exists to detect.
    head, payload, sig = token.split(".")
    payload = payload[:-2] + ("B" if payload.endswith("A") else "A")

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(f"{head}.{payload}.{sig}")


def test_token_signed_with_another_key_is_rejected():
    """An attacker who knows the token FORMAT but not our secret."""
    forged = jwt.encode(
        {"sub": "p.raman", "roles": ["ADMIN"], "exp": time.time() + 3600},
        "a-completely-different-secret", algorithm="HS256",
    )
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(forged)


def test_expired_token_is_rejected():
    """Issued already expired - cleaner than sleeping for an hour."""
    expired = jwt.encode(
        {"sub": "p.raman", "roles": ["MANAGER"], "exp": time.time() - 10},
        settings.jwt_secret, algorithm="HS256",
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)


def test_garbage_is_rejected():
    for bad in ("not-a-token", "", "a.b.c"):
        with pytest.raises((jwt.PyJWTError, ValueError)):
            decode_access_token(bad)


def test_password_hashing_is_one_way():
    raw = "Compliance123!"
    hashed = hash_password(raw)

    assert hashed != raw
    assert hashed.startswith("$2b$")             # bcrypt marker
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong", hashed) is False
    # Random salt per call: two hashes of the same password differ, which is why a
    # rainbow table is useless.
    assert hash_password(raw) != hashed


def test_verify_survives_a_malformed_stored_hash():
    """A truncated or hand-edited hash must return False, not raise - otherwise one
    bad row turns every login into a 500."""
    assert verify_password("anything", "not-a-real-bcrypt-hash") is False
    