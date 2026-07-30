from __future__ import annotations

from typing import Any

from ..grafana import GrafanaClient
from ..grafana.variables import substitute_variables
from .legend import format_legend
from .models import PanelResult, Series
from .reduce import reduce_points
from .timeutil import resolve_range, step_for


async def fetch_panel_data(
    client: GrafanaClient,
    panel: dict[str, Any],
    dashboard_default_ds: Any,
    variables: dict[str, str],
    dashboard_time: dict[str, Any],
) -> PanelResult:
    panel_type = panel.get("type")
    if panel_type == "text":
        return PanelResult(panel=panel)

    ds_field = panel.get("datasource") or dashboard_default_ds
    ds = await client.resolve_datasource(ds_field)
    if ds is None:
        return PanelResult(panel=panel, error="no datasource")

    targets = panel.get("targets") or []
    series: list[Series] = []

    calc = "lastNotNull"
    if panel_type != "timeseries":
        calcs = panel.get("options", {}).get("reduceOptions", {}).get("calcs") or ["lastNotNull"]
        calc = calcs[0]

    try:
        start, end = resolve_range(dashboard_time.get("from"), dashboard_time.get("to"))
        step = step_for(start, end)
        for target in targets:
            expr = target.get("expr")
            if not expr:
                continue
            expr = substitute_variables(expr, variables)
            use_instant = panel_type != "timeseries" and target.get("instant") is True and target.get("range") is not True
            if use_instant:
                for metric, value in await client.query_instant(ds, expr):
                    label = format_legend(target.get("legendFormat"), metric)
                    series.append(Series(label=label, value=value))
                continue
            for metric, points in await client.query_range(ds, expr, start, end, step):
                label = format_legend(target.get("legendFormat"), metric)
                if panel_type == "timeseries":
                    series.append(Series(label=label, points=points))
                else:
                    series.append(Series(label=label, value=reduce_points(points, calc), points=points))
    except Exception as exc:  # noqa: BLE001
        return PanelResult(panel=panel, error=str(exc))

    return PanelResult(panel=panel, series=series)
