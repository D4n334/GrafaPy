from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Series:
    label: str
    value: float | None = None
    points: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class PanelResult:
    panel: dict[str, Any]
    series: list[Series] = field(default_factory=list)
    error: str | None = None
