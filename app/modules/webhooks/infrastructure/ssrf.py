"""SSRF-protected HTTP client for webhook delivery with DNS resolve."""

from __future__ import annotations

import ipaddress
import logging
import socket
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


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        for net in BLOCKED_NETWORKS:
            if ip in net:
                return True
    except ValueError:
        pass
    return False


def is_safe_url(url: str) -> bool:
    """Reject private, loopback and link-local addresses after DNS resolve."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False

        # Resolve all addresses
        try:
            infos = socket.getaddrinfo(hostname, None)
            for info in infos:
                ip = info[4][0]
                if _is_blocked_ip(ip):
                    logger.warning("Blocked SSRF attempt to %s (%s)", url, ip)
                    return False
        except socket.gaierror:
            return False

        return True
    except Exception:
        return False


async def safe_post(url: str, json: dict, headers: dict, timeout: float = 10.0) -> httpx.Response:
    if not is_safe_url(url):
        raise ValueError("Webhook URL blocked by SSRF protection")
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        return await client.post(url, json=json, headers=headers)