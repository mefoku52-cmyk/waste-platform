"""Konfiguracia modelov pre fallback router.

Mená modelov a ich poradie su definovane tu, aby sa dali menit
bez zasahu do logiky. Poradie v zozname urcuje prioritu.
"""

from __future__ import annotations

# Zoznam modelov v poradi priority (prvy = skusa sa ako prvy)
# Meno modelu -> trieda adaptera (bude importovana v fallback_adapter.py)
MODEL_PRIORITY: list[str] = [
    "cerebras",  # najrychlejsi, skusa sa prvy
    "mistral",  # dobry na slovencinu
    "krok",  # zalozny model
]

# Mapovanie mena modelu na triedu adaptera (bude doplnene neskor)
# Toto je len kostra, aby sme vedeli, kam co pojde.
