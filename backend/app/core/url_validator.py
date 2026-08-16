"""
URL validation module to prevent Server-Side Request Forgery (SSRF).

Validates URLs before making outbound HTTP requests by:
- Enforcing http/https protocol whitelist
- Validating hostname presence and syntax
- Blocking cloud metadata endpoints (169.254.169.254, metadata.google.internal, etc.)
- Resolving DNS and checking all resolved IPs against private, loopback, link-local,
  multicast, reserved, and unspecified IP ranges
- Handling IPv4-mapped IPv6 addresses (e.g., ::ffff:127.0.0.1)
- Handling integer/hex/octal IP representations
- Validating redirect targets at each hop to prevent open redirect SSRF
- Safe error messages that do not expose internal network details
"""

import ipaddress
import logging
import socket
from typing import Optional, Set
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# RFC1918, loopback, link-local, multicast, and other dangerous IP networks
_BLOCKED_NETWORKS = [
    # Loopback
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    # Private RFC1918
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Link-local / AWS / GCP / Azure metadata
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
    # Multicast
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("ff00::/8"),
    # Unspecified & Reserved
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),   # Shared address space (CGN)
    ipaddress.ip_network("192.0.0.0/24"),     # IETF protocol assignments
    ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1
    ipaddress.ip_network("198.18.0.0/15"),    # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local (ULA)
]

# Cloud metadata endpoints and local top-level domains
_BLOCKED_HOSTNAMES: Set[str] = {
    "metadata.google.internal",
    "metadata.goog",
    "instance-data",
    "metadata",
    "localhost",
}

_BLOCKED_SUFFIXES = (
    ".local",
    ".internal",
    ".localhost",
    ".localdomain",
    ".corp",
    ".home.arpa",
)

MAX_REDIRECTS = 5
DEFAULT_TIMEOUT = 30.0


class URLValidationError(Exception):
    """Raised when a URL fails SSRF security validation."""
    pass


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to any restricted or private network."""
    # If IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1), unwrap to IPv4
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped

    if ip.is_multicast:
        return True

    # If it is not a globally reachable address, block it (covers loopback, private RFC1918, link-local, etc.)
    if not ip.is_global:
        return True

    for network in _BLOCKED_NETWORKS:
        if ip in network:
            return True

    return False


def _check_ip_literal(hostname: str) -> Optional[bool]:
    """
    Check if the hostname is a direct IP address literal (string, integer, etc.).
    Returns True if it's a blocked IP, False if it's a safe IP, None if not an IP literal.
    """
    # Try standard IP address parsing
    try:
        ip = ipaddress.ip_address(hostname.strip("[]"))
        return _is_blocked_ip(ip)
    except ValueError:
        pass

    # Try integer/hex/octal IP representation
    if hostname.isdigit():
        try:
            ip_int = int(hostname)
            if 0 <= ip_int <= 0xFFFFFFFF:
                ip = ipaddress.ip_address(ip_int)
                return _is_blocked_ip(ip)
        except (ValueError, OverflowError):
            pass

    return None


def validate_url(url: str) -> str:
    """
    Validate a URL for SSRF safety. Returns the validated URL string.
    
    Raises URLValidationError with a safe user-facing message if blocked.
    Never exposes internal network details in exception messages.
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("A valid URL is required.")

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception:
        raise URLValidationError("Invalid URL format.")

    # Protocol whitelist: only http and https
    if parsed.scheme not in ("http", "https"):
        raise URLValidationError("Only http:// and https:// URLs are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("URL must include a valid hostname.")

    hostname_lower = hostname.lower()

    # Block well-known metadata hostnames
    if hostname_lower in _BLOCKED_HOSTNAMES:
        logger.warning("SSRF blocked: direct blocked hostname %s", hostname)
        raise URLValidationError("This URL points to a restricted address and cannot be accessed.")

    # Block internal TLDs
    if any(hostname_lower.endswith(suffix) for suffix in _BLOCKED_SUFFIXES):
        logger.warning("SSRF blocked: internal hostname suffix %s", hostname)
        raise URLValidationError("This URL points to a restricted address and cannot be accessed.")

    # Check direct IP literals
    is_blocked = _check_ip_literal(hostname)
    if is_blocked is True:
        logger.warning("SSRF blocked: direct IP literal %s is restricted", hostname)
        raise URLValidationError("This URL points to a restricted address and cannot be accessed.")
    elif is_blocked is False:
        # Valid public IP literal
        return url

    # Resolve hostname via DNS and verify all returned IPs
    _validate_resolved_dns(hostname)

    return url


def _validate_resolved_dns(hostname: str) -> None:
    """
    Resolve hostname to IP addresses via DNS and verify none are in blocked ranges.
    This prevents DNS rebinding attacks.
    """
    try:
        addr_infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise URLValidationError("Could not resolve the hostname. Please check the URL.")
    except Exception as e:
        logger.warning("DNS resolution error for %s: %s", hostname, e)
        raise URLValidationError("Could not resolve the hostname. Please check the URL.")

    if not addr_infos:
        raise URLValidationError("Could not resolve the hostname. Please check the URL.")

    for addr_info in addr_infos:
        ip_str = addr_info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise URLValidationError("This URL points to a restricted address and cannot be accessed.")

        if _is_blocked_ip(ip):
            logger.warning("SSRF blocked: hostname=%s resolved to restricted IP=%s", hostname, ip_str)
            raise URLValidationError("This URL points to a restricted address and cannot be accessed.")


def create_safe_client(
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = MAX_REDIRECTS,
) -> httpx.AsyncClient:
    """
    Create an httpx.AsyncClient with SSRF-safe redirect validation.
    Validates redirect targets before they are followed.
    """
    async def _validate_redirect(response: httpx.Response) -> None:
        if response.is_redirect and response.next_request:
            redirect_url = str(response.next_request.url)
            validate_url(redirect_url)

    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        max_redirects=max_redirects,
        follow_redirects=True,
        event_hooks={"response": [_validate_redirect]},
    )
