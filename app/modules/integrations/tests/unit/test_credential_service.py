
import pytest
from cryptography.fernet import Fernet

from app.modules.integrations.application.services.credential_service import (
    CredentialService,
)
from app.modules.integrations.infrastructure.encryption.credential_encryptor import (
    CredentialEncryptor,
)


@pytest.fixture
def credential_service(monkeypatch):
    monkeypatch.setenv(
        "INTEGRATIONS_ENCRYPTION_KEY",
        Fernet.generate_key().decode("utf-8"),
    )
    return CredentialService()


def test_credentials_round_trip(credential_service):
    original = {
        "username": "test-user",
        "password": "test-password",
    }

    encrypted = credential_service.secure_credentials(original)

    assert encrypted != str(original)
    assert credential_service.expose_credentials(encrypted) == original


def test_missing_key(monkeypatch):
    monkeypatch.delenv("INTEGRATIONS_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValueError, match="INTEGRATIONS_ENCRYPTION_KEY"):
        CredentialEncryptor()


def test_invalid_key(monkeypatch):
    monkeypatch.setenv("INTEGRATIONS_ENCRYPTION_KEY", "invalid_key")

    with pytest.raises(ValueError, match="Neplatný formát"):
        CredentialEncryptor()


def test_empty_credentials(credential_service):
    with pytest.raises(ValueError):
        credential_service.secure_credentials({})
