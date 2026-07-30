from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DashboardSummary:
    uid: str
    title: str
    folder_title: str | None = None


@dataclass
class Datasource:
    uid: str
    name: str
    type: str
    is_default: bool = False
