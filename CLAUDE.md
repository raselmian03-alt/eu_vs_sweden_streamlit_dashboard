# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit dashboard comparing macroeconomic indicators (inflation, unemployment, GDP, interest rates, population) between Sweden, EU, and Nordic countries using live Eurostat API data.

## Commands

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

No test framework is configured. `test.py` is an exploratory script for Eurostat API experiments, not a test suite.

## Architecture

```
app.py                      → Streamlit entry point, loads data + renders 3 tabs (Sweden, Europe, Comparison)
utils/eurostat_loader.py    → Eurostat API data fetching, caching (@st.cache_data), transformation
modules/charts.py           → Plotly chart builders + Streamlit metric displays
```

**Data flow**: Eurostat REST API → `utils/eurostat_loader.py` (fetch + transform) → `app.py` (orchestrate) → `modules/charts.py` (visualize)

All data is fetched live from Eurostat (no local data files). DataFrames use DatetimeIndex with ISO country code columns (SE, EU, DK, FI, NO).

## Key Patterns

- **Generic loader**: `_load_wide()` in `eurostat_loader.py` handles all Eurostat datasets; specific `load_*()` functions pass dataset-specific filters
- **Caching**: All `load_*()` functions use `@st.cache_data` to avoid redundant API calls
- **Private helpers**: Prefixed with `_` (e.g., `_latest_value()`, `_yoy()`, `_line_chart()`)
- **Geo code normalization**: `EU27_2020` is renamed to `EU` for display
- **Unique widget keys**: All Streamlit widgets use `_safe_key()` to generate unique keys
- **GDP per capita**: Calculated field — combines GDP and population datasets
