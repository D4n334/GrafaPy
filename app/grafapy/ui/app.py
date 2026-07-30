from __future__ import annotations

import asyncio
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, TabbedContent, TabPane

from ..config import load_settings
from ..grafana import GrafanaClient
from ..panels import fetch_panel_data
from .carousel import Carousel
from .dashboard_state import DashboardState
from .layout import mount_panels

_TAB_PREFIX = "tab-"


class GrafaPyApp(App):
    TITLE = "GrafaPy"
    SUB_TITLE = "Grafana in your terminal"

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    VerticalScroll {
        padding: 1;
    }
    .panel-row {
        height: auto;
        margin-bottom: 1;
    }
    .panel-row > PanelView {
        height: 1fr;
        margin-right: 1;
    }
    .panel-row > PanelView:last-child {
        margin-right: 0;
    }
    """

    BINDINGS = [
        ("r", "refresh_current", "Refresh"),
        ("c", "toggle_carousel", "Carousel"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.client = GrafanaClient(self.settings)
        self._dashboards: dict[str, DashboardState] = {}
        self._carousel = Carousel(self.settings.carousel_interval)

    def compose(self) -> ComposeResult:
        yield Header()
        yield TabbedContent(id="tabs")
        yield Footer()

    async def on_mount(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        try:
            summaries = await self.client.search_dashboards()
        except Exception as exc:  # noqa: BLE001
            self.notify(f"Failed to reach Grafana: {exc}", severity="error", timeout=10)
            return

        if not summaries:
            self.notify("No dashboards visible to this token.", severity="warning")
            return

        for summary in summaries:
            state = DashboardState(summary.uid, summary.title)
            self._dashboards[summary.uid] = state
            pane = TabPane(
                summary.title,
                VerticalScroll(id=f"scroll-{summary.uid}"),
                id=f"{_TAB_PREFIX}{summary.uid}",
            )
            await tabs.add_pane(pane)

        self.set_interval(self.settings.refresh_interval, self._refresh_timer_tick)
        self.set_interval(self._carousel.interval, self._carousel_tick)
        self._update_subtitle()
        await self._ensure_dashboard_loaded(summaries[0].uid)

    async def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        pane_id = event.pane.id
        if not pane_id or not pane_id.startswith(_TAB_PREFIX):
            return
        if self._carousel.note_activation(pane_id):
            self._update_subtitle()
        uid = pane_id.removeprefix(_TAB_PREFIX)
        await self._ensure_dashboard_loaded(uid)

    async def _carousel_tick(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_ids = [f"{_TAB_PREFIX}{uid}" for uid in self._dashboards]
        next_id = self._carousel.next_tab(tab_ids, tabs.active)
        if next_id:
            tabs.active = next_id

    def _update_subtitle(self) -> None:
        self.sub_title = f"Grafana in your terminal · {self._carousel.status_text} (press c)"

    async def action_toggle_carousel(self) -> None:
        self._carousel.toggle()
        self._update_subtitle()
        self.notify(f"Carousel {'resumed' if self._carousel.enabled else 'paused'}", timeout=2)

    async def _ensure_dashboard_loaded(self, uid: str) -> None:
        state = self._dashboards.get(uid)
        if state is None or state.loaded or state.loading:
            return
        state.loading = True
        try:
            state.dashboard = await self.client.get_dashboard(uid)
            state.variables = await self.client.resolve_variables(state.dashboard)
            scroll = self.query_one(f"#scroll-{state.uid}", VerticalScroll)
            mount_panels(scroll, state)
            state.loaded = True
            await self._refresh_dashboard(uid)
        except Exception as exc:  # noqa: BLE001
            self.notify(f"Failed to load '{state.title}': {exc}", severity="error", timeout=10)
        finally:
            state.loading = False

    async def _refresh_dashboard(self, uid: str) -> None:
        state = self._dashboards.get(uid)
        if state is None or not state.loaded or state.dashboard is None:
            return
        dashboard_time = state.dashboard.get("time", {})
        default_ds = state.dashboard.get("datasource")

        async def fetch(panel: dict[str, Any]):
            return panel["id"], await fetch_panel_data(
                self.client, panel, default_ds, state.variables, dashboard_time
            )

        panels = list(state.panel_views.keys())
        panel_defs = {p["id"]: p for p in state.dashboard.get("panels", [])}
        results = await asyncio.gather(
            *(fetch(panel_defs[pid]) for pid in panels), return_exceptions=True
        )
        for outcome in results:
            if isinstance(outcome, Exception):
                continue
            panel_id, result = outcome
            view = state.panel_views.get(panel_id)
            if view is not None:
                view.update_result(result)

    async def _refresh_timer_tick(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        active = tabs.active
        if active and active.startswith(_TAB_PREFIX):
            await self._refresh_dashboard(active.removeprefix(_TAB_PREFIX))

    async def action_refresh_current(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        active = tabs.active
        if active and active.startswith(_TAB_PREFIX):
            uid = active.removeprefix(_TAB_PREFIX)
            await self._ensure_dashboard_loaded(uid)
            await self._refresh_dashboard(uid)
            self.notify("Refreshed", timeout=2)

    async def action_quit(self) -> None:
        await self.client.aclose()
        self.exit()


def run() -> None:
    GrafaPyApp().run()


if __name__ == "__main__":
    run()
