from __future__ import annotations

import math
from typing import Any

import httpx

from ..config import Settings
from .models import DashboardSummary, Datasource
from .variables import parse_label_values_query


class GrafanaClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._http = httpx.AsyncClient(
            base_url=settings.grafana_url,
            headers={"Authorization": f"Bearer {settings.grafana_token}"},
            timeout=settings.request_timeout,
        )
        self._datasources: list[Datasource] | None = None

    async def aclose(self) -> None:
        await self._http.aclose()

    async def search_dashboards(self) -> list[DashboardSummary]:
        resp = await self._http.get("/api/search", params={"type": "dash-db"})
        resp.raise_for_status()
        return [
            DashboardSummary(uid=d["uid"], title=d["title"], folder_title=d.get("folderTitle"))
            for d in resp.json()
        ]

    async def get_dashboard(self, uid: str) -> dict[str, Any]:
        resp = await self._http.get(f"/api/dashboards/uid/{uid}")
        resp.raise_for_status()
        return resp.json()["dashboard"]

    async def get_datasources(self) -> list[Datasource]:
        if self._datasources is None:
            resp = await self._http.get("/api/datasources")
            resp.raise_for_status()
            self._datasources = [
                Datasource(uid=d["uid"], name=d["name"], type=d["type"], is_default=d.get("isDefault", False))
                for d in resp.json()
            ]
        return self._datasources

    async def resolve_datasource(self, ds_field: Any) -> Datasource | None:
        datasources = await self.get_datasources()

        if isinstance(ds_field, dict):
            uid = ds_field.get("uid")
            for ds in datasources:
                if ds.uid == uid:
                    return ds
            return None

        if isinstance(ds_field, str):
            for ds in datasources:
                if ds.name == ds_field or ds.uid == ds_field:
                    return ds
            return None

        for ds in datasources:
            if ds.is_default:
                return ds
        return datasources[0] if datasources else None

    async def resolve_variables(self, dashboard: dict[str, Any]) -> dict[str, str]:
        variables: dict[str, str] = {}
        for var in dashboard.get("templating", {}).get("list", []):
            if var.get("type") != "query":
                continue
            name = var["name"]
            query = var.get("query")
            query_str = query.get("query") if isinstance(query, dict) else query
            value = await self._resolve_query_variable(var.get("datasource"), query_str)
            variables[name] = value if value is not None else ".*"
        return variables

    async def _resolve_query_variable(self, ds_field: Any, query_str: str | None) -> str | None:
        if not query_str:
            return None
        parsed = parse_label_values_query(query_str)
        if parsed is None:
            return None
        metric_selector, label = parsed

        ds = await self.resolve_datasource(ds_field)
        if ds is None or ds.type != "prometheus":
            return None

        params = {}
        if metric_selector:
            params["match[]"] = metric_selector
        try:
            resp = await self._http.get(
                f"/api/datasources/proxy/uid/{ds.uid}/api/v1/label/{label}/values",
                params=params,
            )
            resp.raise_for_status()
            values = resp.json().get("data", [])
        except httpx.HTTPError:
            return None
        return values[0] if values else None

    async def query_instant(self, ds: Datasource, expr: str) -> list[tuple[dict[str, str], float]]:
        if ds.type != "prometheus":
            return []
        resp = await self._http.get(
            f"/api/datasources/proxy/uid/{ds.uid}/api/v1/query",
            params={"query": expr},
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "success":
            raise RuntimeError(payload.get("error", "query failed"))

        result = payload["data"]["result"]
        out: list[tuple[dict[str, str], float]] = []
        for series in result:
            metric = series.get("metric", {})
            _, value = series["value"]
            value = float(value)
            if math.isfinite(value):
                out.append((metric, value))
        return out

    async def query_range(
        self, ds: Datasource, expr: str, start: float, end: float, step: float
    ) -> list[tuple[dict[str, str], list[tuple[float, float]]]]:
        if ds.type != "prometheus":
            return []
        resp = await self._http.get(
            f"/api/datasources/proxy/uid/{ds.uid}/api/v1/query_range",
            params={"query": expr, "start": start, "end": end, "step": step},
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "success":
            raise RuntimeError(payload.get("error", "query failed"))

        result = payload["data"]["result"]
        out: list[tuple[dict[str, str], list[tuple[float, float]]]] = []
        for series in result:
            metric = series.get("metric", {})
            points = []
            for ts, v in series["values"]:
                fv = float(v)
                if math.isfinite(fv):
                    points.append((float(ts), fv))
            out.append((metric, points))
        return out
