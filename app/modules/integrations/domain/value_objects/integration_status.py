from enum import Enum


class IntegrationStatus(str, Enum):
    """
    Stav pripojenia k externému systému.

    Stavy:
    - PENDING: Čaká na prvé overenie pripojenia
    - ACTIVE: Pripojenie je funkčné a overené
    - FAILED: Posledné overenie zlyhalo
    - DISCONNECTED: Pripojenie bolo manuálne odpojené
    - RETRYING: Prebieha automatické opakovanie po zlyhaní
    """
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    DISCONNECTED = "disconnected"
    RETRYING = "retrying"
