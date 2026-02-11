import streamlit as st

from modules.charts import (
    big_numbers_block,
    inflation_chart,
    interest_chart,
    unemployment_chart,
    comparison_section,
)

from utils.eurostat_loader import (
    load_inflation,
    load_interest_rates,
    load_unemployment,
    load_population,
    load_gdp,
    load_gdp_per_capita,
)

st.set_page_config(page_title="Sweden vs EU Economic Dashboard", layout="wide")
st.title("📊 Sweden vs EU Economic Dashboard")

# Load data
inflation = load_inflation()
interest = load_interest_rates()
unemp = load_unemployment()
population = load_population()
gdp = load_gdp()
gdp_pc = load_gdp_per_capita()

tab1, tab2, tab3 = st.tabs([" Sweden", "Europe", "📊 Comparison"])

with tab1:
    big_numbers_block("Sweden - Key Numbers", inflation, interest, unemp, population, gdp, gdp_pc, geo="SE")
    st.divider()
    inflation_chart(inflation, key_prefix="tab_se")
    st.divider()
    interest_chart(interest, "SE", key_prefix="tab_se")
    st.divider()
    unemployment_chart(unemp, "SE", key_prefix="tab_se")

with tab2:
    big_numbers_block("Europe - Key Numbers", inflation, interest, unemp, population, gdp, gdp_pc, geo="EU")
    st.divider()
    inflation_chart(inflation, key_prefix="tab_eu")
    st.divider()
    interest_chart(interest, "EU", key_prefix="tab_eu")
    st.divider()
    unemployment_chart(unemp, "EU", key_prefix="tab_eu")

with tab3:
    comparison_section(inflation, interest, unemp, key_prefix="tab_cmp")
