from __future__ import annotations

from typing import Any

from ..widgets.panel_view import PanelView


class DashboardState:
    def __init__(self, uid: str, title: str) -> None:
        self.uid = uid
        self.title = title
        self.dashboard: dict[str, Any] | None = None
        self.variables: dict[str, str] = {}
        self.panel_views: dict[int, PanelView] = {}
        self.loaded = False
        self.loading = False
