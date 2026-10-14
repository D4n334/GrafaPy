from __future__ import annotations

from typing import Any

from textual.containers import Horizontal, VerticalScroll

from ..widgets.panel_view import PanelView
from .dashboard_state import DashboardState


def _panel_height(gridpos_h: int, panel_type: str) -> int:
    if panel_type == "timeseries":
        return max(12, gridpos_h)
    if panel_type == "text":
        return max(5, gridpos_h)
    return max(7, gridpos_h)


def _group_into_rows(panels: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    panels = sorted(
        panels, key=lambda p: (p.get("gridPos", {}).get("y", 0), p.get("gridPos", {}).get("x", 0))
    )
    rows: list[list[dict[str, Any]]] = []
    for panel in panels:
        y = panel.get("gridPos", {}).get("y", 0)
        if rows and rows[-1][0].get("gridPos", {}).get("y", 0) == y:
            rows[-1].append(panel)
        else:
            rows.append([panel])
    return rows


def mount_panels(scroll: VerticalScroll, state: DashboardState) -> None:
    assert state.dashboard is not None
    panels = [p for p in state.dashboard.get("panels", []) if p.get("type") != "row"]

    for row in _group_into_rows(panels):
        row_height = max(_panel_height(p.get("gridPos", {}).get("h", 8), p.get("type", "")) for p in row)
        horizontal = Horizontal(classes="panel-row")
        horizontal.styles.height = row_height + 2
        scroll.mount(horizontal)
        for panel in row:
            width = max(1, panel.get("gridPos", {}).get("w", 24))
            view = PanelView(panel)
            view.styles.width = f"{width}fr"
            horizontal.mount(view)
            state.panel_views[panel["id"]] = view
