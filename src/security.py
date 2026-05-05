"""Production safety helpers for the FastAPI backend."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import logging
import os
import time
from typing import Iterable
from uuid import UUID

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SecuritySettings:
    allowed_origins: list[str]
    backend_api_key: str | None
    max_request_bytes: int
    max_upload_bytes: int
    max_upload_files: int
    rate_limit_requests: int
    rate_limit_window_seconds: int


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        logger.warning("Invalid integer env %s=%r. Falling back to %s", name, os.getenv(name), default)
        return default


def get_security_settings() -> SecuritySettings:
    origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ]
    return SecuritySettings(
        allowed_origins=origins,
        backend_api_key=os.getenv("BACKEND_API_KEY") or None,
        max_request_bytes=_int_env("MAX_REQUEST_BYTES", 2_000_000),
        max_upload_bytes=_int_env("MAX_UPLOAD_BYTES", 8_000_000),
        max_upload_files=_int_env("MAX_UPLOAD_FILES", 5),
        rate_limit_requests=_int_env("RATE_LIMIT_REQUESTS", 60),
        rate_limit_window_seconds=_int_env("RATE_LIMIT_WINDOW_SECONDS", 60),
    )


class InMemoryRateLimiter:
    """Simple process-local rate limiter for local and small single-instance deployments."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max(1, max_requests)
        self.window_seconds = max(1, window_seconds)
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self.requests[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
        bucket.append(now)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def require_backend_api_key(request: Request, settings: SecuritySettings) -> None:
    """Require X-API-Key only when BACKEND_API_KEY is configured."""
    if not settings.backend_api_key:
        return
    provided = request.headers.get("x-api-key")
    if provided != settings.backend_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing backend API key.")


def validate_content_length(request: Request, settings: SecuritySettings) -> None:
    raw_length = request.headers.get("content-length")
    if not raw_length:
        return
    try:
        content_length = int(raw_length)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Content-Length header.")
    if content_length > settings.max_request_bytes:
        raise HTTPException(status_code=413, detail="Request body is too large.")


def validate_uuid(value: str | None, field_name: str, required: bool = True) -> str | None:
    if not value:
        if required:
            raise HTTPException(status_code=400, detail=f"{field_name} is required.")
        return None
    try:
        UUID(value)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a valid UUID.") from error
    return value


def validate_text_length(value: str, field_name: str, max_chars: int, min_chars: int = 1) -> None:
    length = len(value.strip())
    if length < min_chars:
        raise HTTPException(status_code=400, detail=f"{field_name} must contain at least {min_chars} characters.")
    if length > max_chars:
        raise HTTPException(status_code=413, detail=f"{field_name} is too long. Maximum: {max_chars} characters.")


def validate_upload_count(count: int, settings: SecuritySettings) -> None:
    if count > settings.max_upload_files:
        raise HTTPException(status_code=413, detail=f"Too many files. Maximum: {settings.max_upload_files}.")


def validate_upload_bytes(file_bytes: bytes, filename: str, settings: SecuritySettings) -> None:
    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File '{filename}' is too large. Maximum: {settings.max_upload_bytes} bytes.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail=f"File '{filename}' is empty.")


def validate_allowed_mime(mime_type: str | None, filename: str, allowed: Iterable[str]) -> None:
    lower_name = filename.lower()
    normalized = mime_type or ""
    extension_ok = lower_name.endswith((".pdf", ".docx", ".txt", ".md", ".markdown"))
    if normalized in allowed or extension_ok:
        return
    raise HTTPException(status_code=400, detail=f"Unsupported file type for '{filename}'.")


def public_error_message(status_code: int, fallback: str = "Request failed.") -> str:
    """Avoid leaking stack traces or provider internals in 5xx responses."""
    if status_code >= 500:
        return fallback
    return fallback
