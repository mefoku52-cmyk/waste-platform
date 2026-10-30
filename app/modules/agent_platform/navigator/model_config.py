"""Konfiguracia modelov pre fallback router."""

from __future__ import annotations

# Zoznam modelov v poradi priority (prvy = skusa sa ako prvy)
MODEL_PRIORITY: list[str] = [
    "groq",  # najrychlejsi, skvela dostupnost
    "cerebras",  # druhy v poradi
    "mistral",  # treti v poradi
]
