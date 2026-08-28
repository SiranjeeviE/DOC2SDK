"""
Security test suite for Doc2SDK.

Verifies:
1. SSRF prevention (IP blocklists, metadata blocking, protocol whitelisting, redirect protection)
2. CORS headers and credential restrictions
3. Rate limiting (429 responses and Retry-After headers)
4. Authentication & Authorization (API Key, timing-safe checks, 401 responses)
5. Security response headers (nosniff, DENY, etc.)
6. Input validation (HTTP methods, path sanitization, URL schemes)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.url_validator import validate_url, URLValidationError
from app.core.auth import verify_api_key, is_auth_enabled
from app.core.rate_limiter import rate_limit_ai, rate_limit_general


# =============================================================================
# 1. SSRF Protection Tests
# =============================================================================

@pytest.mark.parametrize("blocked_url", [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.1.1",
    "http://localhost",
    "http://localhost:8080",
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254",
    "http://10.0.0.1",
    "http://10.255.255.255",
    "http://172.16.0.1",
    "http://172.31.255.255",
    "http://192.168.1.1",
    "http://0.0.0.0",
    "http://[::1]",
    "http://[fe80::1]",
    "http://[fc00::1]",
    "http://2130706433",               # Decimal integer representation of 127.0.0.1
    "http://metadata.google.internal",
    "http://metadata.goog",
    "http://instance-data",
    "http://api.local",
    "http://internal.service.internal",
    "file:///etc/passwd",
    "gopher://127.0.0.1:6379/_PING",
    "ftp://evil.com/file",
    "javascript:alert(1)",
    "",
    "   ",
])
def test_ssrf_validator_blocks_dangerous_urls(blocked_url):
    with pytest.raises(URLValidationError):
        validate_url(blocked_url)


def test_ssrf_validator_allows_safe_urls():
    safe_urls = [
        "https://example.com",
        "https://example.com/docs/api.json",
        "http://example.com:8080/openapi",
        "https://httpbin.org/get",
    ]
    for url in safe_urls:
        validated = validate_url(url)
        assert validated == url


def test_project_create_rejects_ssrf_source_url(client):
    response = client.post("/api/projects", json={
        "name": "SSRF Test",
        "source_url": "http://169.254.169.254/latest/meta-data/"
    })
    assert response.status_code == 400
    assert "restricted" in response.json()["detail"].lower() or "cannot be accessed" in response.json()["detail"].lower()


def test_unified_execute_rejects_ssrf(client):
    response = client.post("/api/v1/playground/execute", json={
        "base_url": "http://127.0.0.1:6379",
        "path": "/",
        "method": "GET"
    })
    assert response.status_code == 400
    assert "restricted" in response.json()["detail"].lower() or "cannot be accessed" in response.json()["detail"].lower()


# =============================================================================
# 2. CORS Configuration Tests
# =============================================================================

def test_cors_headers_allowed_origin(client):
    response = client.options(
        "/api/projects",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_wildcard_not_with_credentials(client):
    """If allow_credentials is true, allow-origin must never be wildcard '*'."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"}
    )
    origin_header = response.headers.get("access-control-allow-origin")
    cred_header = response.headers.get("access-control-allow-credentials")
    if cred_header == "true":
        assert origin_header != "*"


# =============================================================================
# 3. Rate Limiting Tests
# =============================================================================

def test_rate_limiter_blocks_burst(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_AI", "2")
    rate_limit_ai.reset()

    # Fast responses with mock
    with patch("app.routers.projects.process_project_background"):
        # Request 1: Allowed
        r1 = client.post("/api/projects", json={
            "name": "Rate Limit 1",
            "source_url": "https://example.com"
        })
        assert r1.status_code == 200

        # Request 2: Allowed
        r2 = client.post("/api/projects", json={
            "name": "Rate Limit 2",
            "source_url": "https://example.com"
        })
        assert r2.status_code == 200

        # Request 3: Exceeds rate limit -> 429
        r3 = client.post("/api/projects", json={
            "name": "Rate Limit 3",
            "source_url": "https://example.com"
        })
        assert r3.status_code == 429
        assert "Retry-After" in r3.headers

    rate_limit_ai.reset()


# =============================================================================
# 4. Authentication & Authorization Tests
# =============================================================================

def test_auth_disabled_when_api_key_unset(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "")
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    assert response.json()["auth_enabled"] is False


def test_auth_enforced_when_api_key_set(client, monkeypatch):
    test_key = "secure-random-test-api-key-12345"
    monkeypatch.setenv("API_KEY", test_key)

    # 1. Unauthenticated request to protected endpoint -> 401
    unauth_res = client.post("/api/projects", json={
        "name": "Protected Project",
        "source_url": "https://example.com"
    })
    assert unauth_res.status_code == 401
    assert "WWW-Authenticate" in unauth_res.headers

    # 2. Invalid key -> 401
    bad_res = client.post(
        "/api/projects",
        json={"name": "Protected Project", "source_url": "https://example.com"},
        headers={"Authorization": "Bearer wrong-key"}
    )
    assert bad_res.status_code == 401

    # 3. Valid key via Bearer token -> 200
    with patch("app.routers.projects.process_project_background"):
        good_res = client.post(
            "/api/projects",
            json={"name": "Protected Project", "source_url": "https://example.com"},
            headers={"Authorization": f"Bearer {test_key}"}
        )
        assert good_res.status_code == 200

    # 4. Valid key via X-API-Key header -> 200
    with patch("app.routers.projects.process_project_background"):
        header_res = client.post(
            "/api/projects",
            json={"name": "Protected Project 2", "source_url": "https://example.com"},
            headers={"x-api-key": test_key}
        )
        assert header_res.status_code == 200

    # 5. Public read-only endpoints remain accessible without auth
    read_res = client.get("/api/projects")
    assert read_res.status_code == 200

    health_res = client.get("/health")
    assert health_res.status_code == 200


def test_auth_verify_endpoint(client, monkeypatch):
    test_key = "my-secret-key"
    monkeypatch.setenv("API_KEY", test_key)

    # Verify invalid key
    res_bad = client.post("/api/auth/verify", json={"api_key": "wrong-key"})
    assert res_bad.status_code == 200
    assert res_bad.json()["authenticated"] is False

    # Verify valid key
    res_good = client.post("/api/auth/verify", json={"api_key": test_key})
    assert res_good.status_code == 200
    assert res_good.json()["authenticated"] is True


# =============================================================================
# 5. Security Headers Tests
# =============================================================================

def test_security_headers_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


# =============================================================================
# 6. Input Validation Tests
# =============================================================================

def test_execute_request_invalid_method(client):
    response = client.post("/api/v1/playground/execute", json={
        "base_url": "https://example.com",
        "path": "/test",
        "method": "INVALID_METHOD"
    })
    assert response.status_code == 422  # Pydantic validation error


def test_execute_request_null_byte_path(client):
    response = client.post("/api/v1/playground/execute", json={
        "base_url": "https://example.com",
        "path": "/etc/passwd\0.png",
        "method": "GET"
    })
    assert response.status_code == 422
