"""
Authentication module for Doc2SDK API.

Provides API key-based authentication with constant-time comparison to prevent timing attacks.
Supports optional mode: if API_KEY is unset, authentication is disabled (for local dev).
When API_KEY is set, protected endpoints require Authorization: Bearer <key> or X-API-Key: <key>.
"""

import hmac
import os
from typing import Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_security = HTTPBearer(auto_error=False)


def get_configured_api_key() -> str:
    """Retrieve the configured API key from environment."""
    return os.getenv("API_KEY", "").strip()


def is_auth_enabled() -> bool:
    """Return True if an API_KEY is configured in the environment."""
    return bool(get_configured_api_key())


def verify_api_key(provided_key: Optional[str]) -> bool:
    """
    Verify the provided key against the configured API_KEY.
    Uses constant-time comparison to avoid timing attacks.
    """
    configured_key = get_configured_api_key()
    if not configured_key:
        # Auth is disabled
        return True

    if not provided_key:
        return False

    return hmac.compare_digest(provided_key.strip(), configured_key)


async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_security),
) -> bool:
    """
    FastAPI dependency that enforces API key authentication.
    
    Checks:
    1. Authorization: Bearer <key>
    2. X-API-Key: <key>
    
    If auth is disabled (API_KEY unset), allows all requests.
    If auth is enabled and key is missing/invalid, raises HTTP 401.
    """
    if not is_auth_enabled():
        return True

    provided_key: Optional[str] = None

    # Check Bearer token
    if credentials and credentials.credentials:
        provided_key = credentials.credentials
    # Fallback to X-API-Key header
    elif "x-api-key" in request.headers:
        provided_key = request.headers["x-api-key"]

    if not provided_key or not verify_api_key(provided_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True
