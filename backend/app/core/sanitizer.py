import re
import json
from typing import Any, Dict, Optional

SENSITIVE_HEADER_KEYS = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "api-key",
    "apikey",
    "cookie",
    "set-cookie",
    "token",
    "x-auth-token",
    "x-access-token",
    "access-token",
    "secret",
    "x-secret-key",
    "password",
}

SENSITIVE_FIELD_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"passwd", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"private[_-]?key", re.IGNORECASE),
    re.compile(r"client[_-]?secret", re.IGNORECASE),
    re.compile(r"authorization", re.IGNORECASE),
]

REDACTED = "***REDACTED***"


def is_sensitive_key(key: str) -> bool:
    if not isinstance(key, str):
        return False
    lower_key = key.lower().strip()
    if lower_key in SENSITIVE_HEADER_KEYS:
        return True
    return any(pattern.search(lower_key) for pattern in SENSITIVE_FIELD_PATTERNS)


def sanitize_headers(headers: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    Sanitizes HTTP request or response headers by masking credential keys.
    """
    if not headers or not isinstance(headers, dict):
        return headers

    sanitized = {}
    for k, v in headers.items():
        k_str = str(k)
        if is_sensitive_key(k_str):
            sanitized[k_str] = REDACTED
        else:
            sanitized[k_str] = str(v)
    return sanitized


def sanitize_payload(payload: Any) -> Any:
    """
    Recursively scrubs sensitive fields (passwords, tokens, keys) from arbitrary JSON-serializable payloads.
    """
    if payload is None:
        return None

    if isinstance(payload, dict):
        cleaned = {}
        for k, v in payload.items():
            k_str = str(k)
            if is_sensitive_key(k_str):
                cleaned[k_str] = REDACTED
            else:
                cleaned[k_str] = sanitize_payload(v)
        return cleaned

    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]

    if isinstance(payload, str):
        # Attempt to parse as JSON string if possible
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, (dict, list)):
                return sanitize_payload(parsed)
        except (ValueError, TypeError):
            pass

        # Mask Bearer tokens in plain strings
        masked = re.sub(r'(?i)\bBearer\s+([A-Za-z0-9_\-\.\~]+)', f'Bearer {REDACTED}', payload)
        return masked

    return payload
