# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
streamlit run app.py
```

## Architecture

Single-file Streamlit app (`app.py`) that fetches Brazilian stock data from Yahoo Finance and renders three interactive Plotly charts.

**Data flow:**
1. `load_data()` — cached (`ttl=3600`) call to `yf.download()`, returns a raw DataFrame with potentially a `MultiIndex` column structure when multiple tickers are requested.
2. `get_series()` — normalizes the MultiIndex vs flat column difference so the rest of the code always receives a plain `pd.Series`.
3. Charts and metric cards are built directly in the module body using the sidebar filter state (`selected_names`, `start_date`, `end_date`).

**Tickers** are defined in the `TICKERS` dict (display name → Yahoo Finance symbol, e.g. `"PETR4.SA"`). `COLORS` maps the same display names to hex values used across all charts for visual consistency.

**Charts:**
- Price line chart (`go.Scatter` via `plotly.graph_objects`)
- Cumulative return line chart (same structure, normalized to first close)
- Monthly volume bar chart (`plotly.express.bar`, resampled with `"ME"`)

## Adding a new stock

1. Add an entry to `TICKERS` and `COLORS` in `app.py`.
2. No other changes needed — the sidebar checkboxes, metric cards, and all three charts are generated dynamically from `selected_names`.
