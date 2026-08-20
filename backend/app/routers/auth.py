"""
Authentication router for Doc2SDK API.

Provides endpoints for the frontend to:
- Check if authentication is enabled
- Verify an API key
"""

from typing import Optional
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from ..core.auth import is_auth_enabled, verify_api_key

router = APIRouter(prefix="/auth", tags=["auth"])


class VerifyRequest(BaseModel):
    api_key: Optional[str] = None


class VerifyResponse(BaseModel):
    authenticated: bool
    auth_enabled: bool
    message: str


class AuthStatusResponse(BaseModel):
    auth_enabled: bool


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """Returns whether authentication is required by this server instance."""
    return AuthStatusResponse(auth_enabled=is_auth_enabled())


@router.post("/verify", response_model=VerifyResponse)
async def verify_key(
    request: Request,
    body: Optional[VerifyRequest] = None,
    authorization: Optional[str] = Header(None),
):
    """
    Verify whether the provided API key is valid.
    Checks request body `api_key`, `Authorization: Bearer <token>`, or `X-API-Key`.
    """
    if not is_auth_enabled():
        return VerifyResponse(
            authenticated=True,
            auth_enabled=False,
            message="Authentication is currently disabled on this server.",
        )

    key = None
    if body and body.api_key:
        key = body.api_key
    elif authorization and authorization.startswith("Bearer "):
        key = authorization[7:].strip()
    elif "x-api-key" in request.headers:
        key = request.headers["x-api-key"]

    if key and verify_api_key(key):
        return VerifyResponse(
            authenticated=True,
            auth_enabled=True,
            message="API key is valid.",
        )
    else:
        return VerifyResponse(
            authenticated=False,
            auth_enabled=True,
            message="Invalid API key.",
        )
