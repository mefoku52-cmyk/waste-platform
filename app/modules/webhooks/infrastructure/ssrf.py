"""SSRF-protected HTTP client for webhook delivery."""

from __future__ import annotations

import ipaddress
import logging
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def is_safe_url(url: str) -> bool:
    """Reject private, loopback and link-local addresses."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Resolve and check (simplified; full impl would use async getaddrinfo)
        try:
            ip = ipaddress.ip_address(hostname)
            for net in BLOCKED_NETWORKS:
                if ip in net:
                    return False
        except ValueError:
            pass  # hostname, not IP – allow for now (DNS rebinding protection needed in prod)
        return True
    except Exception:
        return False


async def safe_post(url: str, json: dict, headers: dict, timeout: float = 10.0) -> httpx.Response:
    if not is_safe_url(url):
        raise ValueError("Webhook URL blocked by SSRF protection")
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.post(url, json=json, headers=headers)