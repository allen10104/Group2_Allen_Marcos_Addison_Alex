import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.auth.jwt_utils import create_access_token
from backend.dependencies import (
    authenticate_user,
    create_token_for_user,
    get_current_user,
    USERS_BY_ID,
)


def test_authenticate_user_valid_jane():
    user = authenticate_user("jane.doe@example.com", "password")
    assert user is not None
    assert user.id == 2


def test_authenticate_user_wrong_password():
    assert authenticate_user("jane.doe@example.com", "wrong") is None


def test_authenticate_user_unknown_email():
    assert authenticate_user("nope@example.com", "password") is None


def test_create_token_for_user_round_trip_with_get_current_user():
    user = USERS_BY_ID[2]
    token = create_token_for_user(user)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    resolved = get_current_user(credentials=credentials)
    assert resolved.id == user.id
    assert resolved.email == user.email


def test_get_current_user_bad_token_raises_401():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="not-a-real-token"
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials)
    assert exc_info.value.status_code == 401


def test_get_current_user_unknown_subject_raises_401():
    token = create_access_token(
        user_id=12345, email="ghost@example.com", is_admin=False
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials)
    assert exc_info.value.status_code == 401
