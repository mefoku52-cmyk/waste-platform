import json
import logging
from typing import Any

from app.modules.integrations.infrastructure.encryption.credential_encryptor import (
    CredentialEncryptor,
)

logger = logging.getLogger(__name__)


class CredentialService:
    def __init__(self, encryptor: CredentialEncryptor | None = None):
        self.encryptor = encryptor or CredentialEncryptor()

    def secure_credentials(self, raw_credentials: dict[str, Any]) -> str:
        if not isinstance(raw_credentials, dict) or not raw_credentials:
            raise ValueError("Credentials musia byť neprázdny objekt.")

        try:
            serialized = json.dumps(
                raw_credentials,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        except (TypeError, ValueError):
            logger.warning("Credentials sa nepodarilo serializovať.")
            raise ValueError("Neplatný formát credentials.") from None

        return self.encryptor.encrypt(serialized)

    def expose_credentials(self, encrypted_credentials: str) -> dict[str, Any]:
        try:
            decrypted = self.encryptor.decrypt(encrypted_credentials)
            result = json.loads(decrypted)
        except (ValueError, json.JSONDecodeError):
            logger.warning("Credentials sa nepodarilo bezpečne načítať.")
            raise ValueError("Credentials nie je možné načítať.") from None

        if not isinstance(result, dict):
            raise ValueError("Dešifrované credentials nemajú platný formát.")

        return result
