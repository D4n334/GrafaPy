from __future__ import annotations

import re

from rich.columns import Columns
from rich.text import Text
from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Vertical
from textual.widgets import Digits, Sparkline, Static

from ..panels import PanelResult
from .barutil import bar_row
from .formatting import format_value, threshold_color

_NUMERIC_PREFIX_RE = re.compile(r"^([+-]?\d[\d,]*\.?\d*)(.*)$")


def _split_numeric(formatted: str) -> tuple[str, str]:
    match = _NUMERIC_PREFIX_RE.match(formatted)
    if not match:
        return formatted, ""
    return match.group(1), match.group(2).strip()


class StatPanel(Vertical):
    DEFAULT_CSS = """
    StatPanel {
        align: center middle;
    }
    StatPanel > Digits {
        width: auto;
    }
    StatPanel > #stat-unit {
        width: auto;
        text-align: center;
        height: auto;
    }
    StatPanel > Sparkline {
        width: 100%;
        height: 3;
        margin-top: 1;
    }
    StatPanel > #stat-bars {
        width: 100%;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Digits("", id="stat-digits")
        yield Static("", id="stat-unit")
        yield Sparkline([], id="stat-spark")
        yield Static("", id="stat-bars")

    def _show_hero(self, visible: bool) -> None:
        self.query_one("#stat-digits", Digits).display = visible
        self.query_one("#stat-unit", Static).display = visible
        self.query_one("#stat-spark", Sparkline).display = visible
        self.query_one("#stat-bars", Static).display = not visible

    def update_result(self, result: PanelResult) -> None:
        bars = self.query_one("#stat-bars", Static)

        if result.error:
            self._show_hero(False)
            bars.update(Text(f"error: {result.error}", style="red"))
            return
        if not result.series:
            self._show_hero(False)
            bars.update(Text("no data", style="dim"))
            return

        defaults = result.panel.get("fieldConfig", {}).get("defaults", {})
        unit = defaults.get("unit")
        decimals = defaults.get("decimals")
        thresholds = defaults.get("thresholds")

        if len(result.series) == 1:
            self._render_hero(result.series[0], unit, decimals, thresholds)
            return

        self._show_hero(False)
        values = [s.value for s in result.series if s.value is not None]
        vmax = (max(values) if values else 100) or 100
        rows = [
            bar_row(s.label, s.value, 0.0, vmax, thresholds, unit, decimals, label_width=18, bar_width=18)
            for s in result.series
        ]
        bars.update(Columns(rows, equal=False, column_first=False, padding=(0, 2)))

    def _render_hero(self, series, unit, decimals, thresholds) -> None:
        digits = self.query_one("#stat-digits", Digits)
        unit_label = self.query_one("#stat-unit", Static)
        spark = self.query_one("#stat-spark", Sparkline)

        self._show_hero(True)
        color = threshold_color(series.value, thresholds)
        numeric, suffix = _split_numeric(format_value(series.value, unit, decimals))
        digits.styles.color = color
        digits.update(numeric)
        unit_label.update(Text(suffix, style=f"bold {color}") if suffix else Text(""))

        values = [v for _, v in series.points]
        if len(values) >= 2:
            spark.display = True
            spark.data = values
            spark.min_color = Color.parse(threshold_color(min(values), thresholds))
            spark.max_color = Color.parse(threshold_color(max(values), thresholds))
        else:
            spark.display = False
