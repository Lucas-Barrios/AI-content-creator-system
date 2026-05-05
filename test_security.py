"""Tests for production security helpers.

Run:
  python3 test_security.py
"""

from __future__ import annotations

from fastapi import HTTPException

from src.security import InMemoryRateLimiter, SecuritySettings, validate_text_length, validate_upload_bytes, validate_uuid


def test_uuid_validation() -> None:
    assert validate_uuid("00000000-0000-0000-0000-000000000001", "clientId")
    try:
        validate_uuid("bad-id", "clientId")
    except HTTPException as error:
        assert error.status_code == 400
        assert "valid UUID" in str(error.detail)
    else:
        raise AssertionError("Invalid UUID should fail")


def test_text_length_validation() -> None:
    validate_text_length("hello", "topic", max_chars=10, min_chars=2)
    try:
        validate_text_length("x" * 20, "topic", max_chars=10)
    except HTTPException as error:
        assert error.status_code == 413
    else:
        raise AssertionError("Oversized text should fail")


def test_upload_size_validation() -> None:
    settings = SecuritySettings(
        allowed_origins=["http://localhost:3000"],
        backend_api_key=None,
        max_request_bytes=100,
        max_upload_bytes=5,
        max_upload_files=1,
        rate_limit_requests=10,
        rate_limit_window_seconds=60,
    )
    validate_upload_bytes(b"12345", "test.txt", settings)
    try:
        validate_upload_bytes(b"123456", "test.txt", settings)
    except HTTPException as error:
        assert error.status_code == 413
    else:
        raise AssertionError("Oversized upload should fail")


def test_rate_limiter() -> None:
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
    limiter.check("client")
    limiter.check("client")
    try:
        limiter.check("client")
    except HTTPException as error:
        assert error.status_code == 429
    else:
        raise AssertionError("Rate limit should fail")


def main() -> None:
    test_uuid_validation()
    test_text_length_validation()
    test_upload_size_validation()
    test_rate_limiter()
    print("security tests passed")


if __name__ == "__main__":
    main()
