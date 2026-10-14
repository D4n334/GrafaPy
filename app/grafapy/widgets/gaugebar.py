from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from ..panels import PanelResult
from .barutil import bar_rows


class GaugeBarPanel(Static):
    _result: PanelResult | None = None

    def update_result(self, result: PanelResult) -> None:
        self._result = result
        if result.error:
            self.update(Text(f"error: {result.error}", style="red"))
            return
        if not result.series:
            self.update(Text("no data", style="dim"))
            return

        defaults = result.panel.get("fieldConfig", {}).get("defaults", {})
        unit = defaults.get("unit")
        decimals = defaults.get("decimals")
        thresholds = defaults.get("thresholds")
        vmin = defaults.get("min", 0)
        vmax = defaults.get("max")
        if vmax is None:
            values = [s.value for s in result.series if s.value is not None]
            vmax = (max(values) if values else 100) or 100

        rows = bar_rows(result.series, vmin, vmax, thresholds, unit, decimals, self.size.width)
        self.update(Group(*rows))

    def on_resize(self) -> None:
        if self._result is not None:
            self.update_result(self._result)
