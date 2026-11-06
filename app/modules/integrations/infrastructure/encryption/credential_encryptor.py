import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class CredentialEncryptor:
    def __init__(self):
        key = os.environ.get("INTEGRATIONS_ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "Chýba samostatná premenná INTEGRATIONS_ENCRYPTION_KEY."
            )

        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except (ValueError, TypeError):
            raise ValueError(
                "Neplatný formát INTEGRATIONS_ENCRYPTION_KEY."
            ) from None

    def encrypt(self, plaintext: str) -> str:
        if not isinstance(plaintext, str) or not plaintext:
            raise ValueError("Obsah na šifrovanie nesmie byť prázdny.")

        return self._fernet.encrypt(
            plaintext.encode("utf-8")
        ).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        if not isinstance(ciphertext, str) or not ciphertext:
            raise ValueError("Šifrovaný obsah nesmie byť prázdny.")

        try:
            return self._fernet.decrypt(
                ciphertext.encode("utf-8")
            ).decode("utf-8")
        except InvalidToken:
            logger.warning("Nepodarilo sa overiť šifrovaný údaj.")
            raise ValueError("Neplatný alebo poškodený šifrovaný údaj.") from None
