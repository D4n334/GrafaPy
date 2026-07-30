from __future__ import annotations

import time

from textual_plotext import PlotextPlot

from ..panels import PanelResult


class TimeseriesPanel(PlotextPlot):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._error: str | None = None
        self._no_data = False
        self._loading = True

    def update_result(self, result: PanelResult) -> None:
        self.plt.clear_data()
        self.plt.clear_figure()
        self._loading = False
        self._error = result.error
        self._no_data = not result.error and not result.series

        if not result.error and result.series:
            now = time.time()
            for s in result.series:
                if not s.points:
                    continue
                xs = [round((ts - now) / 60, 2) for ts, _ in s.points]
                ys = [v for _, v in s.points]
                self.plt.plot(xs, ys, label=s.label, marker="braille")
            self.plt.xlabel("minutes ago")

        self.refresh()

    def render(self):  # type: ignore[override]
        from rich.text import Text

        if self._loading:
            return Text("loading...", style="dim")
        if self._error:
            return Text(f"error: {self._error}", style="red")
        if self._no_data:
            return Text("no data", style="dim")
        return super().render()
