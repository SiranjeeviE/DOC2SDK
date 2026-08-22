from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator

ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


class GenerateRequest(BaseModel):
    source_url: str

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("source_url is required and cannot be empty.")
        v = v.strip()
        if len(v) > 2048:
            raise ValueError("source_url exceeds maximum length of 2048 characters.")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("source_url must start with http:// or https://")
        return v


class GenerateResponse(BaseModel):
    name: str
    version: str
    spec: Dict[str, Any]
    sdk_code: str
    test_code: Optional[str] = None
    is_mock: bool = False
    source: Optional[str] = None


class ExecuteRequest(BaseModel):
    base_url: str
    path: str
    method: str
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    json_body: Optional[Dict[str, Any]] = None

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("base_url is required and cannot be empty.")
        v = v.strip()
        if len(v) > 2048:
            raise ValueError("base_url exceeds maximum length of 2048 characters.")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if v is None or not isinstance(v, str):
            return "/"
        v = v.strip()
        if "\0" in v:
            raise ValueError("path cannot contain null bytes.")
        if len(v) > 2048:
            raise ValueError("path exceeds maximum length of 2048 characters.")
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("method is required.")
        upper_method = v.strip().upper()
        if upper_method not in ALLOWED_HTTP_METHODS:
            raise ValueError(f"Invalid HTTP method '{v}'. Must be one of: {', '.join(sorted(ALLOWED_HTTP_METHODS))}")
        return upper_method


class ExecuteResponse(BaseModel):
    status_code: int
    response: Any
