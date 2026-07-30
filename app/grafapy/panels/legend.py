from __future__ import annotations

import re

_LEGEND_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def format_legend(legend_format: str | None, metric: dict[str, str]) -> str:
    if legend_format and legend_format != "__auto":
        return _LEGEND_VAR_RE.sub(lambda m: metric.get(m.group(1), ""), legend_format)

    labels = {k: v for k, v in metric.items() if k != "__name__"}
    if len(labels) == 1:
        return next(iter(labels.values()))
    if labels:
        joined = ", ".join(f"{k}={v}" for k, v in labels.items())
        name = metric.get("__name__")
        return f"{name}{{{joined}}}" if name else joined
    return metric.get("__name__", "value")
