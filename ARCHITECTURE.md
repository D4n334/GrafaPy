# Architecture

This document exists so the code itself can stay comment-free: everything
here used to be scattered across module docstrings and inline comments.
Read this before making structural changes.

## Data flow

1. `ui/app.py` asks `grafana/client.py` for the list of dashboards the
   configured service-account token can see.
2. When a tab is opened for the first time, its dashboard JSON is fetched,
   template variables are resolved, and `ui/layout.py` mounts one widget
   per panel.
3. Every refresh (timer tick, manual `r`, or a freshly-opened tab),
   `panels/fetch.py` re-queries Prometheus for each panel and pushes a
   `PanelResult` into that panel's widget.
4. Widgets in `widgets/` turn a `PanelResult` into terminal output - big
   numbers, horizontal bars, or a `plotext` line chart, depending on panel
   type.

## Module map

- **`config.py`** - loads `GRAFANA_URL` / `GRAFANA_TOKEN` from a `.env`
  file, searching upward from the current file's directory so the app
  works whether it's launched from the repo root or from `app/`.

- **`grafana/`** - everything about talking to the Grafana HTTP API.
  - `client.py` - the async `GrafanaClient`: dashboard discovery, dashboard
    JSON, datasource lookup, and the raw Prometheus queries.
  - `models.py` - `DashboardSummary`, `Datasource`.
  - `variables.py` - two stateless string operations: substituting
    `$var`/`${var}`/`[[var]]` references in a PromQL expression, and
    parsing the `label_values(...)` syntax Grafana uses for "query" type
    template variables.

- **`panels/`** - turning a panel's Grafana query results into renderable
  data.
  - `fetch.py` - the orchestration: resolves the panel's datasource, runs
    its query/queries, and returns a `PanelResult`.
  - `models.py` - `Series` (one queried line/value + its label) and
    `PanelResult` (a panel's title/config plus its series, or an error).
  - `legend.py` - `format_legend`, reproducing Grafana's `legendFormat`
    logic (including the `__auto` special case).
  - `reduce.py` - `reduce_points`, reproducing a panel's
    `reduceOptions.calcs` (stat/gauge/bargauge panels reduce a queried
    range down to one displayed value; see "Range queries" below).
  - `timeutil.py` - parsing Grafana's relative time strings (`now-6h`).

- **`ui/`** - the Textual application layer.
  - `app.py` - `GrafaPyApp`: composes widgets, binds keys, wires
    everything else in this list together. Deliberately thin - anything
    that isn't Textual plumbing lives in one of the other files here.
  - `dashboard_state.py` - `DashboardState`: one tab's raw dashboard JSON,
    resolved template variables, mounted panel widgets, and load status.
  - `layout.py` - `mount_panels`: groups a dashboard's panels into rows by
    their Grafana `gridPos.y` (panels sharing a `y` are one visual row,
    same as Grafana's own dashboard grid) and mounts each row with
    per-panel widths proportional to `gridPos.w`.
  - `carousel.py` - `Carousel`: the auto-advancing tab timer. Kept
    Textual-agnostic (it never touches `TabbedContent` itself, just
    returns which tab id to switch to) so its "was this a manual tab
    switch?" logic is easy to reason about on its own. See "Carousel
    activation dedup" below.

- **`widgets/`** - one file per panel-rendering concern.
  - `stat.py` - `StatPanel`: a single series renders as a big number
    (Textual's `Digits` widget) with a trend `Sparkline` underneath; more
    than one series (a per-consumer/per-route/... breakdown) renders as
    horizontal bars that auto-flow into columns via `rich.columns.Columns`
    so many entries fit without being clipped.
  - `gaugebar.py` - `GaugeBarPanel`: gauge/bargauge panels as hand-rolled
    horizontal bars (see "Why hand-rolled bars" below).
  - `timeseries.py` - `TimeseriesPanel`: a `plotext` line chart.
  - `textpanel.py` - `TextPanel`: Grafana text panels; HTML content is
    stripped down to plain text, markdown is passed through as-is.
  - `barutil.py` - `bar_row`, the shared bar-drawing routine used by both
    `gaugebar.py` and `stat.py`'s multi-series case.
  - `formatting.py` - `format_value`/`threshold_color`: a subset of
    Grafana's field-config unit formatting and threshold-to-colour logic.
  - `panel_view.py` - `PanelView`: the bordered container that picks the
    right widget above for a panel's `type`.

## Design decisions worth knowing

**Range queries, not instant queries.** Every stat/gauge/bargauge panel's
Grafana target has `range: true` (not `instant: true`) and a
`reduceOptions.calcs` (almost always `["lastNotNull"]`). That means
Grafana queries the *same time window* a timeseries panel would and then
reduces each series to one value - it is not asking "what's true right
now". `panels/fetch.py` mirrors this. Querying instant-only was tried
first and badly undercounted busy panels: an instant query only sees
whatever's active in that exact second, while a 6-hour range query catches
every series that was active *at any point* in the window. Confirmed by
querying Prometheus directly - an instant query returned 7 series for one
panel where the matching 6h range query returned 14.

**`__auto` legend format.** Grafana's `legendFormat: "__auto"` is a
sentinel meaning "derive the legend from labels", not literal text to
display. `panels/legend.py` treats it the same as an empty legend format:
a single label uses just its value, multiple labels join as `k=v` pairs.

**Two datasource JSON shapes.** Older dashboards reference a datasource by
plain name (`"datasource": "prometheus"`); newer ones use
`{"type": ..., "uid": ...}`. `GrafanaClient.resolve_datasource` handles
both, plus a bare `None` (falls back to the org's default datasource).

**Carousel activation dedup.** Textual fires `TabActivated` twice for a
tab's initial auto-activation (once immediately, once again shortly
after). `Carousel.note_activation` dedupes on the pane id rather than
event count, and treats the very first activation it ever sees as
non-manual - otherwise the carousel would silently disable itself before
it ever ran.

**Digits needs numeric/unit splitting.** Textual's `Digits` widget only
renders a small fixed character set (`0-9 + - ^ x : A-F $ ² ( )`) in its
big font; anything else (like `%`, `ms`, `d`, `h`) falls back to tiny
plain text mid-render, which looks broken when mixed with the big digits.
`widgets/stat.py`'s `_split_numeric` splits a formatted value like
`"92.5%"` into `("92.5", "%")` so only the numeric part goes through
`Digits`, and the unit renders separately as small text.

**Hand-rolled bars instead of a charting library.** `gauge`/`bargauge`
panels render via `widgets/barutil.py`'s manual Unicode-block bars, not
`plotext`'s native `bar()`. `plotext.bar()` was tried first, but its
per-series `color` list didn't map colours to bars reliably - colours got
scrambled across bars in testing - which is unacceptable for data people
are using to monitor for problems. The hand-rolled version guarantees
each bar's colour matches its own threshold-derived value.

## Adding a new panel type

1. Add a widget class in `widgets/` with an `update_result(self, result:
   PanelResult) -> None` method (see any existing widget for the shape).
2. Register it in `widgets/panel_view.py`'s `_CONTENT_BY_TYPE` dict, keyed
   by Grafana's panel `type` string.
3. If the panel type needs different query semantics (e.g. it isn't
   naturally a range-query-and-reduce like stat/gauge/bargauge, or a raw
   range series like timeseries), extend `panels/fetch.py`.

## Testing

There's no formal test suite yet. Textual ships a headless test harness
(`App.run_test()`, see the [Textual testing docs](https://textual.textualize.io/guide/testing/))
that can drive `GrafaPyApp` against a real or mocked Grafana instance and
inspect each widget's rendered content - that's the natural place to add
coverage.
