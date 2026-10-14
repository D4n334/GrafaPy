from __future__ import annotations

from rich.text import Text

from .formatting import format_value, threshold_color

_FULL = "█"
_EMPTY = "░"


_MIN_BAR = 6
_MAX_BAR = 24


def bar_rows(series, vmin, vmax, thresholds, unit, decimals, width: int) -> list[Text]:
    """Rows fitted to `width` cells: the label gets the space it needs, the bar shrinks first."""
    width = width or 80
    val_w = max(len(format_value(s.value, unit, decimals)) for s in series) + 1
    longest = max(len(s.label) for s in series)
    # ponytail: label wins over bar down to _MIN_BAR; below that labels get ellipsized
    label_w = max(4, min(longest, width - val_w - _MIN_BAR - 2))
    bar_w = max(_MIN_BAR, min(_MAX_BAR, width - val_w - label_w - 2))
    return [
        bar_row(s.label, s.value, vmin, vmax, thresholds, unit, decimals, label_width=label_w, bar_width=bar_w)
        for s in series
    ]


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
    if len(label) > label_width:
        label = label[: label_width - 1] + "…"
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
