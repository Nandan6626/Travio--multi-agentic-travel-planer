import uuid
import pytest
from fastapi import HTTPException
from app.core.security import auth_verifier
from tests.conftest import create_test_jwt


def test_verify_valid_token():
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    payload = auth_verifier.verify_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["aud"] == "authenticated"


def test_verify_expired_token():
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id, expires_in_minutes=-10)
    with pytest.raises(HTTPException) as exc_info:
        auth_verifier.verify_token(token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_verify_invalid_signature():
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id, secret="wrong-secret-key-that-is-at-least-32-bytes-long")
    with pytest.raises(HTTPException) as exc_info:
        auth_verifier.verify_token(token)
    assert exc_info.value.status_code == 401
    assert "signature" in exc_info.value.detail.lower()


def test_verify_invalid_audience():
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id, audience="wrong_audience")
    with pytest.raises(HTTPException) as exc_info:
        auth_verifier.verify_token(token)
    assert exc_info.value.status_code == 401
    assert "audience" in exc_info.value.detail.lower()


def test_verify_malformed_token():
    with pytest.raises(HTTPException) as exc_info:
        auth_verifier.verify_token("not.a.valid.jwt.token")
    assert exc_info.value.status_code == 401


def test_verify_missing_token():
    with pytest.raises(HTTPException) as exc_info:
        auth_verifier.verify_token("")
    assert exc_info.value.status_code == 401


def test_verify_invalid_uuid_subject():
    token = create_test_jwt(user_id="not-a-valid-uuid")  # type: ignore
    with pytest.raises(HTTPException) as exc_info:
        auth_verifier.verify_token(token)
    assert exc_info.value.status_code == 401
    assert "uuid" in exc_info.value.detail.lower()
