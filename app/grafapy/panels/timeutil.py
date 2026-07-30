from __future__ import annotations

import re
import time

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "M": 2592000,
    "y": 31536000,
}

_RELATIVE_RE = re.compile(r"^now(?:-(\d+)([smhdwMy]))?$")


def resolve_time(value: str | None, *, default: str) -> float:
    value = value or default
    match = _RELATIVE_RE.match(value.strip())
    if not match:
        return time.time()
    amount, unit = match.groups()
    now = time.time()
    if amount is None:
        return now
    return now - int(amount) * _UNIT_SECONDS[unit]


def resolve_range(time_from: str | None, time_to: str | None) -> tuple[float, float]:
    start = resolve_time(time_from, default="now-6h")
    end = resolve_time(time_to, default="now")
    if end <= start:
        end = start + 60
    return start, end


def step_for(start: float, end: float, *, target_points: int = 120) -> float:
    span = max(end - start, 1.0)
    step = span / target_points
    return max(step, 1.0)
