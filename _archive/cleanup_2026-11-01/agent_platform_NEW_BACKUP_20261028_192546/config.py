"""Konfiguracia systemu."""

from __future__ import annotations

import os
from pathlib import Path


class Config:
    """Konfiguracia riadiaceho systemu."""

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir) if base_dir else Path.home() / "cmep-riadiaci-system"
        self.cmep_repo = Path(os.environ.get("CMEP_REPO", str(Path.home() / "waste-platform")))
        self.state_dir = self.base_dir / "stav"
        self.output_dir = self.base_dir / "vystupy"
        self.backup_dir = self.base_dir / "zalohy"

    def ensure_dirs(self) -> None:
        for d in [
            self.state_dir,
            self.output_dir,
            self.backup_dir,
            self.base_dir / "data",
            self.base_dir / "dokumentacia",
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        return {
            "base_dir": str(self.base_dir),
            "cmep_repo": str(self.cmep_repo),
            "state_dir": str(self.state_dir),
            "output_dir": str(self.output_dir),
        }
