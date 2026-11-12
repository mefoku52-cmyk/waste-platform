"""HTTP klient streamovacej sluzby (CMEP Streaming) volany z platformy.

Jediný prístup platformy do streamovacieho jadra je cez tento klient
(server-side). Všetky volania sú autorizované hlavičkou X-CMEP-Internal-Key.
Pri chybách selhávame fail-closed (kontrola na strane platformy — streamovacie
jadro nikdy neprija operáciu bez overenia kľúča).
"""

from uuid import UUID

import httpx

from app.core.config import settings


class StreamingServiceClient:
    """Klient pre interné volania platformy → streaming."""

    def __init__(self, base_url: str | None = None, internal_key: str | None = None):
        self.base_url = (
            (base_url or getattr(settings, "CMEP_STREAMING_INTERNAL_URL", "") or "")
            .strip()
            .rstrip("/")
        )
        if not self.base_url:
            public = (getattr(settings, "CMEP_STREAMING_PUBLIC_URL", "") or "").strip().rstrip("/")
            self.base_url = public
        self.internal_key = (
            internal_key or getattr(settings, "CMEP_INTERNAL_API_KEY", "") or ""
        ).strip()
        self.timeout_s = 5.0

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.internal_key)

    async def end_inspection(self, inspection_id: UUID) -> bool:
        """Povýti streaming, aby uzavrel miestnosť pre danej obhliadke (offerId).

        Vrati True ak streaming miestnosť uzavrel (alebo neexistuje), False pri
        chybe sieťovej (best-effort — platformový stav je autoritatívny).
        """
        if not self.is_configured:
            return False
        url = f"{self.base_url}/internal/inspections/{inspection_id}/end"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                res = await client.post(
                    url,
                    headers={"x-cmep-internal-key": self.internal_key},
                )
            return res.status_code == 200
        except Exception:
            return False


def get_streaming_client() -> StreamingServiceClient:
    return StreamingServiceClient()
