"""Strukturovane logovanie so znizenim rizika uniku známych vzorov tajomstiev.

NEZARUCUJE uplnu ochranu. Rediguje zname formaty tajomstiev a citlive
hodnoty vo vnorenych strukturovanych udajoch.
"""

from __future__ import annotations

import logging
import re
from typing import Any

SECRET_PATTERNS = [
    re.compile(
        r"(?i)(password|passwd|pwd|secret|token|api_key|apikey|auth)\s*[=:]\s*\S+", re.IGNORECASE
    ),
    re.compile(r"sk_[a-zA-Z0-9_]{20,}"),
    re.compile(r"pk_[a-zA-Z0-9_]{20,}"),
    re.compile(r"rk_[a-zA-Z0-9_]{20,}"),
    re.compile(r"whsec_[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{30,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"postgres(?:ql)?://\S+"),
]


def _redact_value(value: Any) -> Any:
    """Rediguje tajomstva v hodnote. Rekurzivne pre dict/list."""
    if isinstance(value, str):
        for pat in SECRET_PATTERNS:
            value = pat.sub("[REDACTED]", value)
        return value
    if isinstance(value, dict):
        return {k: _redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(v) for v in value)
    return value


def redact(text: str) -> str:
    """Rediguje zname formaty tajomstiev v texte."""
    for pat in SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def redact_any(value: Any) -> Any:
    """Rediguje tajomstva v lubovoľnej hodnote (str, dict, list, tuple).

    Pouzij na citlive udaje pred ich uložením alebo zobrazením.
    """
    return _redact_value(value)


class SafeLogger:
    """Logger, ktory rediguje zname vzory tajomstiev. Nezaručuje uplnu ochranu."""

    def __init__(self, name: str = "cmep-riadenie", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            self.logger.addHandler(handler)

    def _log(self, level: int, msg: str, **kwargs) -> None:
        redacted_msg = redact(msg)
        redacted_kwargs = {k: _redact_value(v) for k, v in kwargs.items()}
        self.logger.log(level, redacted_msg, extra=redacted_kwargs if redacted_kwargs else None)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)
