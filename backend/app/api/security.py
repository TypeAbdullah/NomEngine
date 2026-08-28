"""
Security & SSRF Protection Module
Guards against Server-Side Request Forgery, private network scanning, and unauthorized admin operations.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config.settings import settings
from app.monitoring.logger import logger

admin_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

# Compile IP networks for fast membership check
BLOCKED_NETWORKS = [ipaddress.ip_network(net) for net in settings.BLOCKED_IP_NETWORKS]


def is_safe_ip(ip_str: str) -> bool:
    """Checks if an IP address is in a safe, public routing range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            return False
        for blocked_net in BLOCKED_NETWORKS:
            if ip in blocked_net:
                return False
        return True
    except ValueError:
        return False


def validate_crawl_url(url: str) -> bool:
    """
    Validates that a URL is safe to fetch:
    1. Must use http or https scheme
    2. Must have a valid hostname
    3. Hostname cannot resolve to private/loopback/blocked IPs (SSRF protection)
    """
    if not settings.SSRF_PROTECTION_ENABLED:
        return True

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Reject direct localhost names
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False

        # Check if hostname is an IP literal
        try:
            ip = ipaddress.ip_address(hostname)
            return is_safe_ip(str(ip))
        except ValueError:
            pass  # Hostname is a domain name, resolve it

        # Resolve domain to IP addresses
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip_resolved = sockaddr[0]
            if not is_safe_ip(ip_resolved):
                logger.warning(
                    "SSRF check failed: domain resolves to blocked IP",
                    extra_data={"domain": hostname, "ip": ip_resolved, "url": url},
                )
                return False

        return True
    except Exception as e:
        logger.warning(f"URL validation error for {url}: {e}")
        return False


async def verify_admin_key(api_key: Optional[str] = Security(admin_api_key_header)) -> bool:
    """Verifies admin authorization token."""
    # In development mode, allow if not set, or match SECRET_KEY
    if settings.ENVIRONMENT == "development" and not api_key:
        return True
    if api_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Admin API Key",
        )
    return True
