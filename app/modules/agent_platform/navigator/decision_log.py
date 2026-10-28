"""Trvala pamäť rozhodnutí - bezpečný denník rozhodnutí CMEP.

Ukladá rozhodnutí, časové údaje, pôvod a odkazy na dôkazy.
Zabezpečuje obnovenie po reštarte, integritu záznamov cez SHA-256,
bezpečné spracovanie poškodených záznamov a atomický zápis.

Nikdy neukladá API kľúče, tokeny ani iné tajemstvá.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|auth)\s*[:=]\s*\S+"),
    re.compile(r"sk_[a-zA-Z0-9_]{20,}"),
    re.compile(r"pk_[a-zA-Z0-9_]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{30,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
]


def _redact(value: Any) -> Any:
    """Redaguje tajemstvá v hodnote."""
    if isinstance(value, str):
        for pat in SECRET_PATTERNS:
            value = pat.sub("[REDACTED]", value)
        return value
    if isinstance(value, dict):
        return {k: _redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


@dataclass(frozen=True)
class DecisionRecord:
    """Jeden záznam rozhodnutí. Nemenný pre integritu."""

    decision_id: str
    timestamp: str
    decision_type: str
    summary: str
    actor: str | None
    provenance: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    blocker: str | None = None
    verified_facts: list[str] = field(default_factory=list)
    unverified_claims: list[str] = field(default_factory=list)
    previous_hash: str | None = None
    record_hash: str | None = None


def _compute_record_hash(record: DecisionRecord) -> str:
    """Vypočíta SHA-256 hash obsahu záznamu (bez record_hash samotného)."""
    data = {
        "decision_id": record.decision_id,
        "timestamp": record.timestamp,
        "decision_type": record.decision_type,
        "summary": record.summary,
        "actor": record.actor,
        "provenance": record.provenance,
        "evidence_refs": record.evidence_refs,
        "blocker": record.blocker,
        "verified_facts": record.verified_facts,
        "unverified_claims": record.unverified_claims,
        "previous_hash": record.previous_hash,
    }
    payload = json.dumps(data, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class DecisionLog:
    """Bezpečný denník rozhodnutí s integritou a atomickým zápisom."""

    MAX_LOG_SIZE = 1_000_000  # 1 MB
    MAX_ARCHIVES = 3

    def __init__(self, log_path: str | Path, authorize: bool = True):
        self.log_path = Path(log_path).expanduser()
        if self.log_path.exists() and self.log_path.is_symlink():
            raise PermissionError("Denník rozhodnutí je symbolický odkaz")
        parent = self.log_path.parent
        if parent.exists() and parent.is_symlink():
            raise PermissionError("Rodičovský adresár denníka je symbolický odkaz")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.log_path.parent / ".decision.lock"
        self._authorize = authorize

    def _check_authorized(self) -> None:
        if not self._authorize:
            raise PermissionError("Zápis do denníka rozhodnutí nie je autorizovaný")

    def _load_all(self) -> list[dict[str, Any]]:
        """Načíta všetky záznamy, preskočí poškodené."""
        if not self.log_path.exists():
            return []
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(str(self.log_path), flags)
        except OSError:
            return []
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                return []
            with os.fdopen(fd, "r", encoding="utf-8") as f:
                records = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                return records
        except OSError:
            return []

    def _verify_integrity(self, records: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Overí integritu reťazca záznamov."""
        errors: list[str] = []
        previous_chain_hash = None
        for i, rec in enumerate(records):
            stored_record_hash = rec.get("record_hash")
            stored_chain_hash = rec.get("chain_hash")
            stored_prev = rec.get("previous_hash")

            # previous_hash musí byť rovná predchádzajúcemu chain_hash
            if stored_prev != previous_chain_hash:
                errors.append(f"Riadok {i}: previous_hash nesúhlasí s reťazcom")

            # record_hash musí byť rovný prepočítanému hash-u obsahu
            try:
                rec_obj = DecisionRecord(
                    decision_id=rec.get("decision_id", ""),
                    timestamp=rec.get("timestamp", ""),
                    decision_type=rec.get("decision_type", ""),
                    summary=rec.get("summary", ""),
                    actor=rec.get("actor"),
                    provenance=rec.get("provenance", {}),
                    evidence_refs=rec.get("evidence_refs", []),
                    blocker=rec.get("blocker"),
                    verified_facts=rec.get("verified_facts", []),
                    unverified_claims=rec.get("unverified_claims", []),
                    previous_hash=rec.get("previous_hash"),
                    record_hash=rec.get("record_hash"),
                )
                computed = _compute_record_hash(rec_obj)
                if stored_record_hash and stored_record_hash != computed:
                    errors.append(f"Riadok {i}: record_hash nesúhlasí")
            except Exception:
                errors.append(f"Riadok {i}: nemožno overiť hash")

            # chain_hash musí byť rovný sha256(previous_chain_hash | record_hash)
            if previous_chain_hash:
                expected_chain = hashlib.sha256(
                    f"{previous_chain_hash}|{stored_record_hash}".encode()
                ).hexdigest()
            else:
                expected_chain = stored_record_hash or ""
            if stored_chain_hash and stored_chain_hash != expected_chain:
                errors.append(f"Riadok {i}: chain_hash nesúhlasí")

            previous_chain_hash = stored_chain_hash
        return len(errors) == 0, errors

    def _append_locked(self, line: str) -> None:
        """Atomický append pod zámkom."""
        self._check_authorized()
        if self.log_path.exists() and self.log_path.stat().st_size >= self.MAX_LOG_SIZE:
            self._rotate_locked()
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._lock_path, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                if self.log_path.is_symlink():
                    raise PermissionError("Denník rozhodnutí je symbolický odkaz")
                fd = os.open(str(self.log_path), flags, 0o600)
                try:
                    info = os.fstat(fd)
                    if not stat.S_ISREG(info.st_mode):
                        raise ValueError("Denník musí byť obyčajný súbor")
                    os.write(fd, line.encode("utf-8"))
                    os.fsync(fd)
                finally:
                    os.close(fd)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

    def _rotate_locked(self) -> None:
        """Rotácia denníka pri prekročení limitu."""
        for i in range(self.MAX_ARCHIVES, 0, -1):
            src = self.log_path.with_suffix(f".jsonl.{i}")
            dst = self.log_path.with_suffix(f".jsonl.{i + 1}")
            if src.exists():
                if i >= self.MAX_ARCHIVES:
                    src.unlink()
                else:
                    os.replace(str(src), str(dst))
        os.replace(str(self.log_path), str(self.log_path.with_suffix(".jsonl.1")))

    def add_decision(
        self,
        decision_id: str,
        decision_type: str,
        summary: str,
        actor: str | None = None,
        provenance: dict[str, Any] | None = None,
        evidence_refs: list[str] | None = None,
        blocker: str | None = None,
        verified_facts: list[str] | None = None,
        unverified_claims: list[str] | None = None,
        previous_hash: str | None = None,
    ) -> DecisionRecord:
        """Prida nový záznam rozhodnutí do denníka."""
        self._check_authorized()
        records = self._load_all()
        previous_chain_hash = None
        if records:
            last = records[-1]
            previous_chain_hash = last.get("chain_hash")

        # Redaguj tajemstvá pred uložením
        safe_provenance = _redact(provenance or {})
        safe_summary = _redact(summary)
        safe_blocker = _redact(blocker) if blocker else None
        safe_verified = [_redact(f) for f in (verified_facts or [])]
        safe_unverified = [_redact(c) for c in (unverified_claims or [])]
        safe_evidence = [_redact(r) for r in (evidence_refs or [])]

        record = DecisionRecord(
            decision_id=decision_id,
            timestamp=datetime.now(UTC).isoformat(),
            decision_type=decision_type,
            summary=safe_summary,
            actor=actor,
            provenance=safe_provenance,
            evidence_refs=safe_evidence,
            blocker=safe_blocker,
            verified_facts=safe_verified,
            unverified_claims=safe_unverified,
            previous_hash=previous_hash or previous_chain_hash,
        )
        record_hash = _compute_record_hash(record)

        if previous_chain_hash:
            chain_hash = hashlib.sha256(f"{previous_chain_hash}|{record_hash}".encode()).hexdigest()
        else:
            chain_hash = record_hash

        entry = {
            "decision_id": record.decision_id,
            "timestamp": record.timestamp,
            "decision_type": record.decision_type,
            "summary": record.summary,
            "actor": record.actor,
            "provenance": record.provenance,
            "evidence_refs": record.evidence_refs,
            "blocker": record.blocker,
            "verified_facts": record.verified_facts,
            "unverified_claims": record.unverified_claims,
            "previous_hash": record.previous_hash,
            "record_hash": record_hash,
            "chain_hash": chain_hash,
        }
        line = json.dumps(entry, sort_keys=True, ensure_ascii=True) + "\n"
        self._append_locked(line)
        return DecisionRecord(
            decision_id=record.decision_id,
            timestamp=record.timestamp,
            decision_type=record.decision_type,
            summary=record.summary,
            actor=record.actor,
            provenance=record.provenance,
            evidence_refs=record.evidence_refs,
            blocker=record.blocker,
            verified_facts=record.verified_facts,
            unverified_claims=record.unverified_claims,
            previous_hash=record.previous_hash,
            record_hash=record_hash,
        )

    def load_decisions(self) -> list[DecisionRecord]:
        """Načíta všetky platné záznamy rozhodnutí."""
        raw_records = self._load_all()
        decisions: list[DecisionRecord] = []
        for rec in raw_records:
            try:
                decisions.append(
                    DecisionRecord(
                        decision_id=rec.get("decision_id", ""),
                        timestamp=rec.get("timestamp", ""),
                        decision_type=rec.get("decision_type", ""),
                        summary=rec.get("summary", ""),
                        actor=rec.get("actor"),
                        provenance=rec.get("provenance", {}),
                        evidence_refs=rec.get("evidence_refs", []),
                        blocker=rec.get("blocker"),
                        verified_facts=rec.get("verified_facts", []),
                        unverified_claims=rec.get("unverified_claims", []),
                        previous_hash=rec.get("previous_hash"),
                        record_hash=rec.get("record_hash"),
                    )
                )
            except Exception:
                continue
        return decisions

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Overí integritu celého denníka."""
        records = self._load_all()
        return self._verify_integrity(records)

    def get_last_hash(self) -> str | None:
        """Vráti hash posledného záznamu (pre reťazenie integrity)."""
        records = self._load_all()
        if not records:
            return None
        last = records[-1]
        return last.get("chain_hash")
