from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget

from ..panels import PanelResult
from .gaugebar import GaugeBarPanel
from .stat import StatPanel
from .textpanel import TextPanel
from .timeseries import TimeseriesPanel

_CONTENT_BY_TYPE = {
    "stat": StatPanel,
    "gauge": GaugeBarPanel,
    "bargauge": GaugeBarPanel,
    "timeseries": TimeseriesPanel,
    "text": TextPanel,
}


class PanelView(Container):
    DEFAULT_CSS = """
    PanelView {
        border: round $primary-lighten-1;
        padding: 0 1;
    }
    PanelView > GaugeBarPanel {
        content-align: center middle;
        height: 1fr;
    }
    PanelView > StatPanel {
        height: 1fr;
    }
    """

    def __init__(self, panel: dict[str, Any], **kwargs) -> None:
        super().__init__(**kwargs)
        self._panel = panel
        content_cls = _CONTENT_BY_TYPE.get(panel.get("type"), StatPanel)
        self._content: Widget = content_cls()
        title = panel.get("title") or panel.get("type", "panel")
        self.border_title = title

    def compose(self) -> ComposeResult:
        yield self._content

    def update_result(self, result: PanelResult) -> None:
        self._content.update_result(result)
