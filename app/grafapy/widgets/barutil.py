from __future__ import annotations

from rich.text import Text

from .formatting import format_value, threshold_color

_FULL = "█"
_EMPTY = "░"


def bar_row(
    label: str,
    value: float | None,
    vmin: float,
    vmax: float,
    thresholds: dict | None,
    unit: str | None,
    decimals: int | None,
    *,
    label_width: int = 20,
    bar_width: int = 24,
) -> Text:
    color = threshold_color(value, thresholds)
    amount = value if value is not None else 0.0
    span = max(vmax - vmin, 1e-9)
    frac = max(0.0, min(1.0, (amount - vmin) / span))
    filled = round(frac * bar_width)

    text = Text()
    text.append(f"{label:<{label_width}.{label_width}} ", style="dim")
    text.append(_FULL * filled, style=color)
    text.append(_EMPTY * (bar_width - filled), style="grey30")
    text.append(f" {format_value(value, unit, decimals)}", style=f"bold {color}")
    return text
