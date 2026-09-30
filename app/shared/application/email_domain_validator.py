"""Reject obviously fake email domains.

Pydantic EmailStr already checks RFC syntax, but accepts TLDs like
"c", "b.c", "test", "local" that no real MTA can deliver to.
This validator adds a pragmatic blacklist to prevent registration
spam via throwaway/invalid domains.
"""

from __future__ import annotations

# TLDs a domény, ktoré nikdy nemôžu doručiť email.
# Referencie: RFC 2606, RFC 6761, RFC 6762.
_BLOCKED_TLDS = {
    "c",  # a@b.c — dvojznakový fake
    "test",  # .test — rezervované
    "example",  # .example
    "invalid",  # .invalid
    "localhost",  # .localhost
    "local",  # .local (mDNS)
    "onion",  # .onion (Tor)
    "internal",
}

_BLOCKED_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
}


def is_fake_email(email: str) -> bool:
    """True ak email má zjavne fake doménu."""
    if not email or "@" not in email:
        return True
    domain = email.rsplit("@", 1)[1].strip().lower()
    if not domain or "." not in domain:
        return True
    tld = domain.rsplit(".", 1)[1]
    if tld in _BLOCKED_TLDS:
        return True
    return domain in _BLOCKED_DOMAINS


def validate_email_domain(email: str) -> str:
    """Vráti email alebo vyhodí ValueError s dôvodom."""
    if is_fake_email(email):
        raise ValueError(
            "Email domain is not a valid public domain. Please use a real email address."
        )
    return email
