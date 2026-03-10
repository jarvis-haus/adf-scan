from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    scanner_url: str
    scan_dir: Path = Path("/scans")
    poll_interval: float = 5.0
    scan_resolution: int = 300
    scan_color_mode: str = "RGB24"
    scan_duplex: bool = False

    @property
    def scan_source(self) -> str:
        return "AdfDuplex" if self.scan_duplex else "Adf"

    @classmethod
    def from_env(cls) -> Config:
        scanner_url = os.environ.get("SCANNER_URL")
        if not scanner_url:
            raise SystemExit("SCANNER_URL environment variable is required")

        scanner_url = scanner_url.rstrip("/")

        return cls(
            scanner_url=scanner_url,
            scan_dir=Path(os.environ.get("SCAN_DIR", "/scans")),
            poll_interval=float(os.environ.get("POLL_INTERVAL", "5")),
            scan_resolution=int(os.environ.get("SCAN_RESOLUTION", "300")),
            scan_color_mode=os.environ.get("SCAN_COLOR_MODE", "RGB24"),
            scan_duplex=os.environ.get("SCAN_DUPLEX", "").lower() in ("1", "true", "yes"),
        )
