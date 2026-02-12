import streamlit as st

from modules.charts import (
    big_numbers_block,
    inflation_chart,
    inflation_yoy_chart,
    interest_chart,
    interest_rate_bar_chart,
    interest_detail_chart,
    unemployment_chart,
    unemployment_detail_chart,
    gdp_per_capita_chart,
    gdp_pc_comparison_bar,
    debt_to_gdp_chart,
    comparison_section,
)

from utils.eurostat_loader import (
    load_inflation,
    load_inflation_yoy,
    load_interest_rates,
    load_interest_rates_detail,
    load_unemployment,
    load_unemployment_detail,
    load_population,
    load_gdp,
    load_gdp_per_capita,
    load_debt_to_gdp,
    prefetch_all,
)

st.set_page_config(page_title="Sweden vs EU Economic Dashboard", layout="wide")
st.title("📊 Sweden vs EU Economic Dashboard")
st.markdown(
    "A macroeconomic dashboard comparing **Sweden** and the **EU**, "
    "with data pulled directly from [Eurostat](https://ec.europa.eu/eurostat). "
    "Use the tabs below to explore country-specific data or compare across regions."
)

# Fetch all datasets in parallel → saved to local .data_cache/ as parquet
with st.spinner("Loading data from Eurostat (first time only)..."):
    prefetch_all()

# Load data (reads from local parquet cache — instant)
inflation = load_inflation()
inflation_yoy = load_inflation_yoy()
interest = load_interest_rates()
unemp = load_unemployment()
population = load_population()
gdp = load_gdp()
gdp_pc = load_gdp_per_capita()
debt = load_debt_to_gdp()
unemp_detail_se = load_unemployment_detail(geo="SE")
interest_detail_se = load_interest_rates_detail(geo="SE")

tab1, tab2, tab3 = st.tabs(["🇸🇪 Sweden", "🇪🇺 Europe", "📊 Comparison"])

with tab1:
    st.markdown(
        "Detailed economic indicators for **Sweden**, including inflation, interest rates, "
        "unemployment (with gender & age breakdowns), GDP per capita, and government debt. "
        "Most data covers **1990 -- present**; inflation starts from 1996 (when HICP was introduced)."
    )
    big_numbers_block("Sweden - Key Numbers", inflation, interest, unemp, population, gdp, gdp_pc, geo="SE")
    st.divider()
    inflation_yoy_chart(inflation_yoy, geo="SE", key_prefix="tab_se")
    st.divider()
    inflation_chart(inflation, geo="SE", key_prefix="tab_se")
    st.divider()
    interest_chart(interest, "SE", key_prefix="tab_se")
    st.divider()
    interest_rate_bar_chart(interest, "SE", years=5, key_prefix="tab_se")
    st.divider()
    interest_detail_chart(interest_detail_se, years=5, key_prefix="tab_se")
    st.divider()
    unemployment_chart(unemp, "SE", key_prefix="tab_se")
    st.divider()
    unemployment_detail_chart(unemp_detail_se, key_prefix="tab_se")
    st.divider()
    gdp_per_capita_chart(gdp_pc, "SE", years=15, key_prefix="tab_se")
    st.divider()
    debt_to_gdp_chart(debt, geo="SE", key_prefix="tab_se")

with tab2:
    st.markdown(
        "Key economic indicators for the **European Union** (EU27). "
        "Covers inflation, government bond yields, unemployment, GDP per capita, and public debt. "
        "Some EU-aggregate series start later than individual countries (e.g. unemployment from 2000, GDP from 1995)."
    )
    big_numbers_block("Europe - Key Numbers", inflation, interest, unemp, population, gdp, gdp_pc, geo="EU")
    st.divider()
    inflation_yoy_chart(inflation_yoy, geo="EU", key_prefix="tab_eu")
    st.divider()
    inflation_chart(inflation, geo="EU", key_prefix="tab_eu")
    st.divider()
    interest_chart(interest, "EU", key_prefix="tab_eu")
    st.divider()
    interest_rate_bar_chart(interest, "EU", years=5, key_prefix="tab_eu")
    st.divider()
    unemployment_chart(unemp, "EU", key_prefix="tab_eu")
    st.divider()
    gdp_per_capita_chart(gdp_pc, "EU", years=15, key_prefix="tab_eu")
    st.divider()
    debt_to_gdp_chart(debt, geo="EU", key_prefix="tab_eu")

with tab3:
    st.markdown(
        "Side-by-side comparison of **Sweden, EU, Denmark, Finland, and Norway** across all indicators. "
        "Use the country selector below to choose which regions to include. "
        "Note: Norway is missing from interest rates and government debt (not an EU member, data not in Eurostat)."
    )
    comparison_section(inflation, interest, unemp, population, gdp_pc, debt, inflation_yoy, key_prefix="tab_cmp")
    st.divider()
    gdp_pc_comparison_bar(gdp_pc, key_prefix="tab_cmp")
