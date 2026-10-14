from __future__ import annotations


def reduce_points(points: list[tuple[float, float]], calc: str) -> float | None:
    if not points:
        return None
    values = [v for _, v in points]
    calc = (calc or "lastNotNull").lower()
    if calc in ("lastnotnull", "last"):
        return values[-1]
    if calc in ("firstnotnull", "first"):
        return values[0]
    if calc == "min":
        return min(values)
    if calc == "max":
        return max(values)
    if calc in ("mean", "avg"):
        return sum(values) / len(values)
    if calc in ("sum", "total"):
        return sum(values)
    if calc == "count":
        return float(len(values))
    return values[-1]
