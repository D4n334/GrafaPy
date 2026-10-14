from __future__ import annotations

from typing import Any

_GRAFANA_COLOR_TO_RICH = {
    "green": "green",
    "red": "red",
    "yellow": "yellow",
    "orange": "dark_orange",
    "blue": "blue",
    "purple": "purple",
    "light-blue": "bright_blue",
    "dark-red": "dark_red",
    "dark-green": "dark_green",
    "dark-yellow": "dark_goldenrod",
    "dark-orange": "dark_orange3",
    "dark-purple": "dark_magenta",
    "super-light-green": "light_green",
    "semi-dark-green": "dark_green",
    "text": "white",
}


def rich_color(grafana_color: str | None) -> str:
    if not grafana_color:
        return "white"
    return _GRAFANA_COLOR_TO_RICH.get(grafana_color, grafana_color)


def threshold_color(value: float | None, thresholds: dict[str, Any] | None) -> str:
    if value is None or not thresholds:
        return "white"
    steps = thresholds.get("steps") or []
    color = "green"
    for step in steps:
        step_value = step.get("value")
        if step_value is None or value >= step_value:
            color = step.get("color", color)
        else:
            break
    return rich_color(color)


_UNIT_SUFFIXES = {
    "percent": "%",
    "percentunit": "%",
    "s": "s",
    "ms": "ms",
    "reqps": " req/s",
    "bps": "bps",
    "short": "",
    "none": "",
    "locale": "",
}

_SI_PREFIXES = [
    (1e12, "T"),
    (1e9, "G"),
    (1e6, "M"),
    (1e3, "K"),
]


def format_value(value: float | None, unit: str | None = None, decimals: int | None = None) -> str:
    if value is None:
        return "N/A"

    unit = unit or "short"

    if unit == "percentunit":
        value = value * 100

    if unit == "s":
        return _format_duration(value)

    if unit == "ms":
        return _format_duration(value / 1000.0)

    if unit in ("bytes", "decbytes"):
        return _format_bytes(value)

    suffix = _UNIT_SUFFIXES.get(unit, f" {unit}" if unit not in ("short", "none") else "")

    if unit in ("percent", "percentunit"):
        return f"{value:.{decimals if decimals is not None else 1}f}{suffix}"

    magnitude = abs(value)
    if unit in ("short", "none") and magnitude >= 1000:
        for threshold, prefix in _SI_PREFIXES:
            if magnitude >= threshold:
                return f"{value / threshold:.{decimals if decimals is not None else 2}f}{prefix}{suffix}"

    if decimals is not None:
        return f"{value:.{decimals}f}{suffix}"

    if float(value).is_integer():
        return f"{int(value)}{suffix}"
    return f"{value:.2f}{suffix}"


def _format_duration(seconds: float) -> str:
    if seconds < 0:
        return f"-{_format_duration(-seconds)}"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {int(sec)}s"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{int(hours)}h {int(minutes)}m"
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h"


def _format_bytes(value: float) -> str:
    for threshold, prefix in [(1 << 40, "TiB"), (1 << 30, "GiB"), (1 << 20, "MiB"), (1 << 10, "KiB")]:
        if abs(value) >= threshold:
            return f"{value / threshold:.2f} {prefix}"
    return f"{value:.0f} B"
