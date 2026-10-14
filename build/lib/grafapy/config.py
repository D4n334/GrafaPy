from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    grafana_url: str
    grafana_token: str
    refresh_interval: float = 15.0
    request_timeout: float = 10.0
    carousel_interval: float = 6.0


def load_settings() -> Settings:
    url = os.environ.get("GRAFANA_URL", "").rstrip("/")
    token = os.environ.get("GRAFANA_TOKEN", "")

    if not url or not token:
        raise RuntimeError(
            "GRAFANA_URL and GRAFANA_TOKEN must be set (create a .env file, "
            "see .env.example)."
        )

    refresh = float(os.environ.get("GRAFAPY_REFRESH_INTERVAL", "15"))
    timeout = float(os.environ.get("GRAFAPY_REQUEST_TIMEOUT", "10"))
    carousel = float(os.environ.get("GRAFAPY_CAROUSEL_INTERVAL", "6"))

    return Settings(
        grafana_url=url,
        grafana_token=token,
        refresh_interval=refresh,
        request_timeout=timeout,
        carousel_interval=carousel,
    )
