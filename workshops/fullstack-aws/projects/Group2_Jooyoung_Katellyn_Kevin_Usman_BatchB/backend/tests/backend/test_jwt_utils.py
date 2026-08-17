from datetime import datetime, timedelta, timezone

import jwt
import pytest

from backend.auth import jwt_utils


def test_create_access_token_returns_string():
    token = jwt_utils.create_access_token(
        user_id=2, email="jane@example.com", is_admin=False
    )
    assert isinstance(token, str)
    assert len(token) > 10


def test_decode_round_trip():
    token = jwt_utils.create_access_token(
        user_id=2, email="jane@example.com", is_admin=False
    )
    payload = jwt_utils.decode_access_token(token)
    assert payload["sub"] == "2"
    assert payload["email"] == "jane@example.com"
    assert payload["is_admin"] is False


def test_tampered_token_raises():
    token = jwt_utils.create_access_token(
        user_id=2, email="jane@example.com", is_admin=False
    )
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(jwt.PyJWTError):
        jwt_utils.decode_access_token(tampered)


def test_wrong_secret_raises():
    token = jwt.encode(
        {
            "sub": "2",
            "email": "jane@example.com",
            "is_admin": False,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "some-other-secret-key-not-the-test-one!!",
        algorithm="HS256",
    )
    with pytest.raises(jwt.PyJWTError):
        jwt_utils.decode_access_token(token)


def test_expired_token_raises():
    token = jwt.encode(
        {
            "sub": "2",
            "email": "jane@example.com",
            "is_admin": False,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        jwt_utils.JWT_SECRET,
        algorithm=jwt_utils.JWT_ALGORITHM,
    )
    with pytest.raises(jwt.PyJWTError):
        jwt_utils.decode_access_token(token)
