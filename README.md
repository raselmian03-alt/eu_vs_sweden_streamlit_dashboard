# Sweden vs EU Economic Dashboard

A Streamlit dashboard comparing macroeconomic indicators between **Sweden**, the **European Union**, and Nordic neighbours (**Denmark**, **Finland**, **Norway**). All data is pulled directly from [Eurostat](https://ec.europa.eu/eurostat).

## Dashboard Tabs

### Sweden
- Key numbers (inflation, interest, unemployment, population, GDP per capita)
- Inflation rate (YoY %) and HICP index
- Government bond yield (line chart + 5-year bar chart)
- Money market interest rates overview (day-to-day, 1/3/6-month, 10Y bond)
- Unemployment rate with gender and age group breakdowns
- GDP per capita (last 15 years)
- Government debt-to-GDP

### Europe
- Same indicators as Sweden but for the EU27 aggregate
- Note: some EU-level data starts later (unemployment from 2000, GDP from 1995)

### Comparison
- Side-by-side charts for Sweden, EU, Denmark, Finland, and Norway
- Country selector to choose which regions to compare
- Covers: inflation, interest rates, unemployment, population, GDP per capita, government debt

## Data Sources

All data comes from [Eurostat](https://ec.europa.eu/eurostat) via the `eurostat` Python package:

| Dataset | Eurostat Code | Coverage |
|---|---|---|
| Inflation (HICP) | `prc_hicp_midx` | 1996 -- present |
| Unemployment | `une_rt_m` | 1990 -- present (EU from 2000) |
| Population | `demo_pjan` | 1990 -- present |
| GDP | `nama_10_gdp` | 1990 -- present (EU from 1995) |
| Govt bond yield | `irt_lt_mcby_m` | 1990 -- present (no Norway) |
| Money market rates | `irt_st_m` | 1990 -- present |
| Govt debt-to-GDP | `gov_10dd_edpt1` | 1995 -- present (no Norway) |

### Known Data Limitations
- **Norway** is not available in Eurostat interest rate or government debt datasets (not an EU member)
- **EU unemployment** data only starts from 2000
- **Inflation (HICP)** was introduced in 1996 -- no earlier data exists

## Project Structure

```
app.py                    # Streamlit entry point (3 tabs)
modules/charts.py         # All Plotly chart functions
utils/eurostat_loader.py  # Data fetching, caching, and transformation
requirements.txt          # Python dependencies
.data_cache/              # Local parquet cache (auto-generated, gitignored)
```

## Setup & Run

```bash
# Clone the repo
git clone https://github.com/raselmian03-alt/eu_vs_sweden_streamlit_dashboard.git
cd eu_vs_sweden_streamlit_dashboard

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The first run fetches all datasets from Eurostat (~10-15 seconds) and caches them locally as parquet files. Subsequent runs load from cache instantly. Cache refreshes automatically after 6 hours.

## Tech Stack

- **Streamlit** -- web dashboard framework
- **Plotly** -- interactive charts with range sliders
- **pandas** -- data manipulation
- **eurostat** -- Eurostat REST API client
- **pyarrow** -- parquet file caching
