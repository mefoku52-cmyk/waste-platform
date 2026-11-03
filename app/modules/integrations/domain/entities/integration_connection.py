from dataclasses import dataclass
from datetime import datetime

from app.modules.integrations.domain.value_objects.integration_status import IntegrationStatus


@dataclass
class IntegrationConnection:
    """
    Doménový objekt predstavujúci pripojenie firmy k externému systému.
    
    Atribúty:
    - id: Unikátny identifikátor pripojenia
    - company_id: Identifikátor firmy (String(36) podľa CMEP štandardu)
    - integration_type: Typ integrácie (napr. "erp_sap", "warehouse_wms")
    - status: Aktuálny stav pripojenia
    - encrypted_credentials: Zašifrované prihlasovacie údaje
    - last_sync_at: Čas poslednej úspešnej synchronizácie
    - created_at: Čas vytvorenia
    - updated_at: Čas poslednej aktualizácie
    """
    id: str
    company_id: str
    integration_type: str
    status: IntegrationStatus
    encrypted_credentials: str | None = None
    last_sync_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
