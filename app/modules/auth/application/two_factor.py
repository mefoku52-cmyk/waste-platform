"""2FA (TOTP) service — Google Authenticator kompatibilne."""

from __future__ import annotations

import json
import secrets
import string
from dataclasses import dataclass
from datetime import UTC, datetime

import pyotp
import qrcode
import qrcode.image.svg
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.infrastructure.models import User2FAModel

ISSUER = "CMEP"
BACKUP_CODE_COUNT = 8
BACKUP_CODE_LENGTH = 8


@dataclass(slots=True)
class TwoFactorSetupResult:
    secret: str
    otpauth_uri: str
    qr_svg: str


@dataclass(slots=True)
class TwoFactorStatus:
    enabled: bool
    verified_at: datetime | None


def _generate_backup_codes() -> list[str]:
    alphabet = string.ascii_uppercase + string.digits
    codes = []
    for _ in range(BACKUP_CODE_COUNT):
        code = "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(2))
        codes.append(code)
    return codes


class TwoFactorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def status(self, *, user_id: str) -> TwoFactorStatus:
        row = await self._session.get(User2FAModel, str(user_id))
        if row is None:
            return TwoFactorStatus(enabled=False, verified_at=None)
        return TwoFactorStatus(
            enabled=bool(row.enabled),
            verified_at=row.verified_at,
        )

    async def is_enabled(self, *, user_id: str) -> bool:
        row = await self._session.get(User2FAModel, str(user_id))
        return bool(row and row.enabled)

    async def setup(self, *, user_id: str, email: str) -> TwoFactorSetupResult:
        """Vygeneruje novy secret a vrati QR + otpauth URI.

        Riadok sa ulozi, ale 'enabled' ostava False, kym user neoveri
        prvy kod cez 'verify_and_enable'.
        """
        secret = pyotp.random_base32()
        otpauth_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=ISSUER,
        )

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
            image_factory=qrcode.image.svg.SvgPathImage,
        )
        qr.add_data(otpauth_uri)
        qr.make(fit=True)
        img = qr.make_image()
        svg_bytes = img.to_string()
        qr_svg = svg_bytes.decode("utf-8")

        now = datetime.now(UTC)
        row = await self._session.get(User2FAModel, str(user_id))
        if row is None:
            row = User2FAModel(
                user_id=str(user_id),
                secret=secret,
                enabled=False,
                backup_codes=None,
                verified_at=None,
                created_at=now,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.secret = secret
            row.enabled = False
            row.backup_codes = None
            row.verified_at = None
            row.updated_at = now

        await self._session.commit()

        return TwoFactorSetupResult(
            secret=secret,
            otpauth_uri=otpauth_uri,
            qr_svg=qr_svg,
        )

    async def verify_and_enable(self, *, user_id: str, code: str) -> tuple[bool, list[str]]:
        """Overi prvy TOTP kod a aktivuje 2FA. Vrati (ok, backup_codes)."""
        row = await self._session.get(User2FAModel, str(user_id))
        if row is None:
            return False, []

        normalized = (code or "").strip().replace(" ", "")
        if not normalized.isdigit() or len(normalized) != 6:
            return False, []

        totp = pyotp.TOTP(row.secret)
        if not totp.verify(normalized, valid_window=1):
            return False, []

        codes = _generate_backup_codes()
        row.enabled = True
        row.backup_codes = json.dumps(codes)
        row.verified_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        await self._session.commit()
        return True, codes

    async def verify_code(self, *, user_id: str, code: str) -> bool:
        """Overi TOTP alebo backup kod pri logine."""
        row = await self._session.get(User2FAModel, str(user_id))
        if row is None or not row.enabled:
            return False

        normalized = (code or "").strip().replace(" ", "").upper()

        # TOTP (6 cislic)
        if normalized.isdigit() and len(normalized) == 6:
            totp = pyotp.TOTP(row.secret)
            return bool(totp.verify(normalized, valid_window=1))

        # Backup kod (XXXX-XXXX)
        if row.backup_codes:
            try:
                codes: list[str] = json.loads(row.backup_codes)
            except (TypeError, ValueError):
                codes = []
            if normalized in codes:
                codes.remove(normalized)
                row.backup_codes = json.dumps(codes)
                row.updated_at = datetime.now(UTC)
                await self._session.commit()
                return True

        return False

    async def disable(self, *, user_id: str, code: str) -> bool:
        row = await self._session.get(User2FAModel, str(user_id))
        if row is None:
            return True
        ok = await self.verify_code(user_id=user_id, code=code)
        if not ok:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True

    async def regenerate_backup_codes(self, *, user_id: str, code: str) -> list[str] | None:
        row = await self._session.get(User2FAModel, str(user_id))
        if row is None or not row.enabled:
            return None
        ok = await self.verify_code(user_id=user_id, code=code)
        if not ok:
            return None
        codes = _generate_backup_codes()
        row.backup_codes = json.dumps(codes)
        row.updated_at = datetime.now(UTC)
        await self._session.commit()
        return codes
