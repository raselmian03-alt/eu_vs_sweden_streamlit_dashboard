import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def _latest_value(x):
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    if isinstance(x, pd.Series):
        x = x.dropna()
        if x.empty:
            return None
        return float(x.iloc[-1])
    try:
        return float(x)
    except Exception:
        return None


def _yoy(series: pd.Series, periods=12):
    series = series.dropna()
    if len(series) < periods + 1:
        return None
    return (series.iloc[-1] / series.iloc[-1 - periods] - 1) * 100


def _safe_key(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in s)


def _line_chart(df, title, y_title, cols_to_plot, name_map=None, key="chart"):
    name_map = name_map or {}

    # only cols
    cols_ok = []
    for c in cols_to_plot:
        if c in df.columns and df[c].dropna().shape[0] > 0:
            cols_ok.append(c)

    if len(cols_ok) == 0:
        st.info("No data available for this chart (filters/dataset may not include this country).")
        return

    fig = go.Figure()
    for c in cols_ok:
        series = df[c].dropna()
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            mode="lines",
            name=name_map.get(c, c)
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title=y_title,
        hovermode="x unified",
        template="plotly_white",
        legend_title_text=""
    )
    fig.update_xaxes(rangeslider_visible=True)

    #  Unique key 
    st.plotly_chart(fig, use_container_width=True, key=_safe_key(key))


def big_numbers_block(title, inflation_df, interest_df, unemp_df, pop_df, gdp_df, gdp_pc_df, geo):
    st.subheader(title)

    c1, c2, c3, c4, c5 = st.columns(5)

    # Inflation YoY
    if geo in inflation_df.columns:
        yoy = _yoy(inflation_df[geo], 12)
        last = _latest_value(inflation_df[geo])
        c1.metric("Inflation YoY", "—" if yoy is None else f"{yoy:.2f}%", "Index" if last is None else f"Index {last:.1f}")
    else:
        c1.metric("Inflation YoY", "—")

    # Interest
    if geo in interest_df.columns:
        last = _latest_value(interest_df[geo])
        c2.metric("Interest (latest)", "—" if last is None else f"{last:.2f}")
    else:
        c2.metric("Interest (latest)", "—")

    # Unemployment
    if geo in unemp_df.columns:
        last = _latest_value(unemp_df[geo])
        c3.metric("Unemployment (latest)", "—" if last is None else f"{last:.2f}%")
    else:
        c3.metric("Unemployment (latest)", "—")

    # Population
    if geo in pop_df.columns:
        last = _latest_value(pop_df[geo])
        c4.metric("Population (latest)", "—" if last is None else f"{last:,.0f}")
    else:
        c4.metric("Population (latest)", "—")

    # GDP per capita
    if geo in gdp_pc_df.columns:
        last = _latest_value(gdp_pc_df[geo])
        c5.metric("GDP per capita", "—" if last is None else f"{last:,.0f} EUR")
    else:
        c5.metric("GDP per capita", "—")


def inflation_chart(inflation_df, geo=None, key_prefix=""):
    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}
    cols = [geo] if geo else ["SE", "EU"]
    label = name_map.get(geo, "") if geo else ""
    st.header(f"Inflation (HICP Index){' — ' + label if label else ''}")
    _line_chart(
        inflation_df,
        "HICP Index (2015=100)",
        "Index (2015=100)",
        cols,
        name_map=name_map,
        key=f"{key_prefix}_inflation"
    )


def inflation_yoy_chart(yoy_df, geo=None, key_prefix=""):
    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}
    cols = [geo] if geo else ["SE", "EU"]
    label = name_map.get(geo, "") if geo else ""
    st.header(f"Inflation Rate (YoY %){' — ' + label if label else ''}")
    _line_chart(
        yoy_df,
        "Annual inflation rate (YoY % change)",
        "% change",
        cols,
        name_map=name_map,
        key=f"{key_prefix}_inflation_yoy"
    )


def interest_chart(interest_df, geo, key_prefix=""):
    st.header("Govt Bond Yield")
    _line_chart(
        interest_df,
        f"Long-term govt bond yield ({geo})",
        "Yield %",
        [geo],
        name_map={"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"},
        key=f"{key_prefix}_interest_{geo}"
    )


def unemployment_chart(unemp_df, geo, key_prefix=""):
    st.header("Unemployment rate")
    _line_chart(
        unemp_df,
        f"Unemployment rate ({geo})",
        "%",
        [geo],
        name_map={"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"},
        key=f"{key_prefix}_unemp_{geo}"
    )


def gdp_per_capita_chart(gdp_pc_df, geo, years=15, key_prefix=""):
    st.header("GDP per Capita")
    cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
    df_recent = gdp_pc_df[gdp_pc_df.index >= cutoff]

    if geo not in df_recent.columns or df_recent[geo].dropna().empty:
        st.info("No GDP per capita data available.")
        return

    series = df_recent[geo].dropna()
    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=series.index.year,
        y=series.values,
        name=name_map.get(geo, geo),
    ))
    fig.update_layout(
        title=f"GDP per capita — last {years} years ({name_map.get(geo, geo)})",
        xaxis_title="Year",
        yaxis_title="EUR / person",
        hovermode="x unified",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True, key=_safe_key(f"{key_prefix}_gdp_pc_{geo}"))


def interest_rate_bar_chart(interest_df, geo, years=5, key_prefix=""):
    st.header("Govt Bond Yield — Last 5 Years")
    cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
    df_recent = interest_df[interest_df.index >= cutoff]

    if geo not in df_recent.columns or df_recent[geo].dropna().empty:
        st.info("No interest rate data available.")
        return

    # Resample to yearly average for a clean bar chart
    yearly = df_recent[geo].resample("YE").mean().dropna()
    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yearly.index.year,
        y=yearly.values.round(2),
        name=name_map.get(geo, geo),
        text=[f"{v:.2f}%" for v in yearly.values],
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Avg govt bond yield — last {years} years ({name_map.get(geo, geo)})",
        xaxis_title="Year",
        yaxis_title="Yield %",
        hovermode="x unified",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True, key=_safe_key(f"{key_prefix}_int_bar_{geo}"))


def interest_detail_chart(detail_df, years=5, key_prefix=""):
    st.header("Interest Rates Overview — Last 5 Years")
    cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
    df_recent = detail_df[detail_df.index >= cutoff]

    cols = [c for c in detail_df.columns if c in df_recent.columns and df_recent[c].dropna().shape[0] > 0]
    if not cols:
        st.info("No interest rate detail data available.")
        return

    _line_chart(
        df_recent,
        "Money market & government bond rates",
        "Rate %",
        cols,
        key=f"{key_prefix}_int_detail"
    )
    st.caption("Source: Eurostat (irt_st_m, irt_lt_mcby_m). Mortgage/consumer loan rates not available in Eurostat.")


def debt_to_gdp_chart(debt_df, geo=None, key_prefix=""):
    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}
    label = name_map.get(geo, "") if geo else ""
    st.header(f"Government Debt-to-GDP{' — ' + label if label else ''}")
    if geo:
        cols = [geo] if geo in debt_df.columns else []
    else:
        cols = [c for c in ["SE", "EU", "DK", "FI", "NO"] if c in debt_df.columns]
    _line_chart(
        debt_df,
        "Government gross debt (% of GDP)",
        "% of GDP",
        cols,
        name_map=name_map,
        key=f"{key_prefix}_debt_gdp"
    )


def gdp_pc_comparison_bar(gdp_pc_df, key_prefix=""):
    st.header("GDP per Capita — Latest Year Comparison")
    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}
    all_geos = ["SE", "EU", "DK", "FI", "NO"]
    cols = [c for c in all_geos if c in gdp_pc_df.columns]

    # Get latest non-null value for each country
    values = {}
    for c in cols:
        s = gdp_pc_df[c].dropna()
        if not s.empty:
            values[name_map.get(c, c)] = s.iloc[-1]

    if not values:
        st.info("No GDP per capita data available.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(values.keys()),
        y=list(values.values()),
        text=[f"{v:,.0f}" for v in values.values()],
        textposition="outside",
    ))
    fig.update_layout(
        title="GDP per capita comparison (latest year, EUR/person)",
        xaxis_title="",
        yaxis_title="EUR / person",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True, key=_safe_key(f"{key_prefix}_gdp_pc_cmp"))


def unemployment_detail_chart(detail_df, key_prefix=""):
    st.header("Sweden Unemployment — Gender & Age")

    st.subheader("By Gender")
    _line_chart(
        detail_df,
        "Unemployment rate by gender (Sweden)",
        "%",
        ["Total", "Men", "Women"],
        key=f"{key_prefix}_unemp_gender"
    )

    st.subheader("By Age Group")
    _line_chart(
        detail_df,
        "Unemployment rate by age group (Sweden)",
        "%",
        ["Total", "Under 25", "25-74"],
        key=f"{key_prefix}_unemp_age"
    )


def comparison_section(inflation_df, interest_df, unemp_df, pop_df, gdp_pc_df, debt_df, inflation_yoy_df, key_prefix=""):
    st.header("Comparison")

    all_opts = ["SE", "EU", "DK", "FI", "NO"]
    available = [c for c in all_opts if (c in inflation_df.columns or c in interest_df.columns or c in unemp_df.columns)]

    selected = st.multiselect(
        "Select countries/regions",
        options=available,
        default=[c for c in ["SE", "EU", "DK", "FI", "NO"] if c in available],
        key=f"{key_prefix}_cmp_select"
    )

    name_map = {"SE": "Sweden", "EU": "Europe", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}

    st.subheader("Inflation Rate (YoY %)")
    _line_chart(inflation_yoy_df, "Annual inflation rate comparison", "% change", selected, name_map, key=f"{key_prefix}_cmp_infl_yoy")
    st.caption("Data available from 1997 (HICP introduced 1996, YoY needs 12 months history).")

    st.subheader("Inflation (HICP Index)")
    _line_chart(inflation_df, "HICP Index comparison", "Index (2015=100)", selected, name_map, key=f"{key_prefix}_cmp_inflation")
    st.caption("Data available from 1996 (HICP framework introduced in 1996).")

    st.subheader("Interest rate")
    _line_chart(interest_df, "Interest comparison", "Yield %", selected, name_map, key=f"{key_prefix}_cmp_interest")
    st.caption("Norway is not available in Eurostat interest rate datasets (not an EU member).")

    st.subheader("Unemployment")
    _line_chart(unemp_df, "Unemployment comparison", "%", selected, name_map, key=f"{key_prefix}_cmp_unemp")
    st.caption("EU data available from 2000 only. Other countries from 1990.")

    st.subheader("Population")
    _line_chart(pop_df, "Population comparison", "Persons", selected, name_map, key=f"{key_prefix}_cmp_pop")

    st.subheader("GDP per Capita")
    _line_chart(gdp_pc_df, "GDP per capita comparison", "EUR / person", selected, name_map, key=f"{key_prefix}_cmp_gdp_pc")
    st.caption("EU from 1995, Sweden from 1993. Earlier data not available in Eurostat.")

    st.subheader("Government Debt (% of GDP)")
    _line_chart(debt_df, "Debt-to-GDP comparison", "% of GDP", selected, name_map, key=f"{key_prefix}_cmp_debt")
    st.caption("Norway not available. Denmark from 2000. Sweden/Finland/EU from 1995.")
