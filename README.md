# GrafaPy
A lightweight Grafana dashboard viewer for the terminal, built with [Textual](https://textual.textualize.io/).

GrafaPy doesn't screenshot Grafana - it reads each dashboard's panel definitions,
runs the underlying PromQL queries directly against your datasources (through
Grafana's datasource proxy), and renders real charts natively in the terminal
(line charts via [plotext](https://github.com/piccolomo/plotext), stat tiles,
gauges and bar gauges).

Supported panel types:
- `stat`: a single series is a big number (with a trend sparkline below it);
  multiple series (a per-consumer/per-route/... breakdown) render as
  horizontal bars that auto-flow into columns so many entries fit.
- `timeseries`: line charts via [plotext](https://github.com/piccolomo/plotext).
- `gauge` / `bargauge`: horizontal bar plots.
- `text`.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the pieces fit together and
the reasoning behind the less-obvious decisions (e.g. why panels are
queried as a time range and reduced, rather than queried instantly).

## Setup

Requires Python 3.10+.

```sh
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .
```

Copy `.env.example` to `.env` and fill in your Grafana URL and a
[service account token](https://grafana.com/docs/grafana/latest/administration/service-accounts/)
with viewer access:

```
GRAFANA_URL=http://your-grafana-host
GRAFANA_TOKEN=glsa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

`.env` is gitignored - never commit real credentials.

## Run

```sh
grafapy
```

or, without installing the entry point:

```sh
python -m grafapy
```

## Usage

- Tabs across the top switch between every dashboard the token can see.
- A carousel automatically cycles through every dashboard tab every 6s, so
  the app works as a passive wallboard out of the box. Switching tabs
  manually pauses it; press `c` to resume.
- Data for a dashboard is fetched the first time you open its tab, then
  refreshed automatically every 15s (configurable via `GRAFAPY_REFRESH_INTERVAL`
  in `.env`).
- `r` forces an immediate refresh of the current tab, `c` toggles the
  carousel, `q` quits.

## Notes / limitations

- Only Prometheus datasources are queried today (the panels seen in this repo's
  target Grafana instance are all Prometheus-backed). Loki panels are skipped.
- Dashboard template variables (`$var`) are resolved once per dashboard load,
  using the first value returned by the variable's `label_values(...)` query.
  Multi-value variables and non-`label_values` variable queries aren't
  supported yet.
- Layout is derived from each panel's Grafana grid position but is simplified
  into stacked rows rather than a pixel-perfect 24-column grid.
